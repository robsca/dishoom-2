# Rota Creator
class Esteban_:
    def __init__(self, constraint):
        self.constraint = constraint

    def make_it_binary(self, constraint):
        '''
        make the constraint binary
        '''
        if not constraint:
            constraint = self.constraint
        else:
            constraint = constraint
        const_ = []
        for const in constraint:
            if const >=0:
                const = 1
            else:
                const = 0
            const_.append(const)
        return const_

    def populate_layer_1(self, layer):
        '''
        Take every layer and divide it into groups
        retur a list of groups
        '''
        layer_full = True if sum(layer) == len(layer) else False
        if layer_full:
            groups = []
            #st.write('This layer is full')
            # start == index of the first 1
            indexes_of_ones = [i for i, x in enumerate(layer) if x == 1]
            groups.append(indexes_of_ones)
            # choose random length
        else:
            # get the index of all zeros
            indexes_of_zeros = [i for i, x in enumerate(layer) if x == 0]
            # get the index of all ones
            indexes_of_ones = [i for i, x in enumerate(layer) if x == 1]
            start = indexes_of_ones[0]
            groups = []
            group = []
            for i, element in enumerate(indexes_of_ones):
                if i < len(indexes_of_ones)-1:
                    if indexes_of_ones[i+1] == element+1:
                        group.append(element)
                    else:
                        group.append(element)
                        groups.append(group)
                        group = []
                else:
                    group.append(element)
                    groups.append(group)  
        return groups

    def random_splitter(self, group, len_shifts):
        '''
        This is the core of the problem
        '''
        import random
        shifts = []
        hours_to_cover = len(group) 
        while hours_to_cover > 0:
            len_shift = random.choice(len_shifts)
            if hours_to_cover >= len_shift:
                shift = [group[0], group[0]+len_shift]
                shifts.append(shift)
                group = group[len_shift:]
                hours_to_cover -= len_shift
            else:
                shift = [group[0], group[0] + hours_to_cover]
                shifts.append(shift)
                hours_to_cover = 0


        copy_of_shifts = shifts.copy()
        shifts_ok = []
        shift_to_review = []

        for shift in copy_of_shifts:
            if shift[1] - shift[0] not in len_shifts: # if the shift is not in the allowed lengths
                shift_to_review.append(shift)
            else:
                shifts_ok.append(shift)

        # now merge the ok shifts with the shift to review
        if len(shift_to_review) > 0:
            for shift in shifts_ok:
                start = shift[0]
                end = shift[1]
                # get all the starting times of the shift to review
                starts_to_review = [i[0] for i in shift_to_review]

                if end in starts_to_review:
                    # get the shifts that needs to be merges
                    index_end = starts_to_review.index(end)
                    shift_to_merge = shift_to_review[index_end]
                    # create a new shift
                    new_shift = [start, shift_to_merge[1]]
                    # remove shift from the list of shifts
                    shifts_ok.remove(shift)
                    shifts_ok.append(new_shift)
                
        return shifts_ok
        
    def populate_layer_2(self, groups, min_hours, max_hours):
        '''
        Take the group and transform it into shifts
        '''
        lenghts_allowed = [i for i in range(int(min_hours), int(max_hours)+1)]
        shifts = []
        
        for group in groups:
            #st.write('Transform this group into a series of shifts: ')
            #st.write(group)
            shifts_ = self.random_splitter(group, lenghts_allowed)
            for shift in shifts_:
                shifts.append(shift)

        return shifts

    def process_rota(self, shifts):
        '''
        take all the shifts and create a hour by hour totals array for plotting
        '''
        rota = []
        for shift in shifts:
            hours = [i for i in range(shift[0], shift[1])]
            rota.extend(hours)
        unique_hours = list(set(rota))
        unique_hours.sort()
        # count the number of hours per day
        rota = [rota.count(i) for i in unique_hours]
        return rota

    def solving_(self, open_time, min_hours, max_hours):
        '''
        create a layer structure for the problem
        '''
        stop = [-1 for i in range(len(self.constraint))]
        new_constraint = self.constraint.copy()
        layers = []
        while max(new_constraint) != 0:
            new_constraint = [element-1 for element in new_constraint]
            constraint_layer = self.make_it_binary(new_constraint)
            layers.append(constraint_layer)
        self.layers = layers
        # obtain all the groups to transform in shifts
        groups = []
        shift_to_add_later = []
        for i, layer in enumerate(layers):
            print('layer: ', i)
            print(layer)
            print('----------------')
            if len(layer) > 0:
                group_in_layer = self.populate_layer_1(layer)
                print('group in layer: ', group_in_layer)
                for group in group_in_layer:
                    print('group: ', group)
                    if len(group) < 4:
                        print('This group is too short')
                        print(f'group: {group}')
                        print('----------------')
                        shift_to_add_later.append(group)
                print('----------------')
                groups.extend(group_in_layer)
            else:
                print('This layer is too short to be processed')
                shift_to_add_later.append(layer)

        shifts = self.populate_layer_2(groups, min_hours, max_hours)
        # process the shifts to align with open and close time
        shifts = [[shift[0]+open_time, shift[1]+open_time] for shift in shifts]
        
        ''''''
        # for all the shift to add later add a shift of min hours at the center
        for shift in shift_to_add_later:
            if len(shift) > 0:
                shift = [shift[0]+open_time, shift[0]+open_time+min_hours]
                shifts.append(shift)
                
        self.rota = self.process_rota(shifts)  
        self.shifts = shifts 
        self.groups = groups
        return self.rota, shifts


