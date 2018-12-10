"""
1. Read and Deserialize input data from file
2. Validate building plans
3. Construct buildings
4. Write result to file
"""
import copy
import math


def empty_matrix(h, w):
    matrix = []
    for i in range(h):
        matrix.append(['.' for j in range(w)])
    return matrix


class CityPlan:
    def __init__(self, h, w):
        self.w = w
        self.h = h
        self.residental_building = []
        self.utility_building = []
        self.plan = empty_matrix(self.h, self.w)
        self.value = 0

    def get_building_quantity(self):
        return len(self.residental_building) + len(self.utility_building)


class City:
    def __init__(self, h, w, distance, qprojects):
        self.w = w
        self.h = h
        self.distance = distance
        self.qprojects = qprojects

        self.projects = []
        self.residental_projects = []
        self.utility_projects = []

        self.residental_building = []
        self.utility_building = []
        self.plan = empty_matrix(self.h, self.w)

    @classmethod
    def deserialize(cls, data):
        data = data.split(' ')
        h, w, distance, qprojects = [int(item) for item in data]
        return cls(h, w, distance, qprojects)

    def add_project(self, project):
        self.projects.append(project)

        if isinstance(project, ResidentalProject):
            self.residental_projects.append(project)

        elif isinstance(project, UtilityProject):
            self.utility_projects.append(project)

    def get_free_cell(self):
        free_cell = []
        for i in range(self.h):
            for j in range(self.w):
                if self.plan[i][j] == '.':
                    free_cell.append((i, j))
        return free_cell

    def check_distance(self, p1, p2):
        distance = None
        for point_1 in p1.filtered_cell:
            for point_2 in p2.filtered_cell:
                distance = math.fabs(point_1[0] - point_2[0]) + math.fabs(point_1[1] - point_2[1])
                if distance <= self.distance:
                    return True

        return False

    def get_last_free_cell(self):
        for i in range(self.h):
            for j in range(self.w):
                if self.plan[self.h - 1 - i][self.w - 1 - j] == '.':
                    return self.h - 1 - i, self.w - 1 - j
        return False

    def construct_scenario(self):
        city_plan = CityPlan(self.w, self.h)
        residental_projects = copy.copy(self.residental_projects)
        utility_projects = copy.copy(self.utility_projects)
        finished = False
        while not finished:
            free_cell = self.get_free_cell()
            empty_cell = False

            if residental_projects:
                residental_project = copy.copy(residental_projects.pop())

                residental_projects_not_contruct = True

                while residental_projects_not_contruct and free_cell:
                    updated_cells, filtered_cell = self.construct_building(free_cell.pop(0), residental_project)
                    if updated_cells:
                        residental_project.coord = updated_cells
                        residental_project.filtered_cell = filtered_cell
                        city_plan.residental_building.append(residental_project)
                        city_plan.plan = self.plan
                        residental_projects_not_contruct = False
                        break

            else:
                empty_cell = True

            if not residental_projects and free_cell and not free_cell[0] == self.get_last_free_cell():
               residental_projects = copy.copy(self.residental_projects)

            free_cell = self.get_free_cell()
            if utility_projects:
                utility_project = utility_projects.pop()

                utility_projects_not_contruct = True

                while utility_projects_not_contruct and free_cell:
                    updated_cells, filtered_cell = self.construct_building(free_cell.pop(0), utility_project)
                    if updated_cells:
                        utility_project.coord = updated_cells
                        utility_project.filtered_cell = filtered_cell
                        city_plan.utility_building.append(utility_project)
                        city_plan.plan = self.plan
                        utility_projects_not_contruct = False
                        break
                else:
                    empty_cell = True

            if empty_cell:
                finished = True
                break

        return city_plan

    def get_utility_building(self):
        pass

    def construct(self):
        city_plan = self.construct_scenario()
        value = 0
        utility_services = {}
        for utility_builing in city_plan.utility_building:
            utility_services[utility_builing.service] = []
            i = 0
            for residental_building in city_plan.residental_building:

                if i in utility_services[utility_builing.service]:
                    i += 1
                    continue

                if self.check_distance(residental_building, utility_builing):

                    utility_services[utility_builing.service].append(i)
                    value += residental_building.capacity
                i += 1

        city_plan.value = value

        return city_plan

    def construct_building(self, start_point, project):
        updated_cell = []
        filtered_cell = []

        def undolog_plan():
            for x_cell, y_cell in updated_cell:
                self.plan[x_cell][y_cell] = '.'

        for x, y in project.coord:
            _x, _y = (x + start_point[0], y + start_point[1])

            try:

                if not self.plan[_x][_y] == '.':
                    undolog_plan()
                    return False, False
                else:
                    updated_cell.append((_x, _y))
                    self.plan[_x][_y] = project.plan[x][y]
                    if project.plan[x][y] == '#':
                        filtered_cell.append((_x, _y))

            except IndexError as e:
                undolog_plan()
                return False, False

        return updated_cell, filtered_cell


class ProjectAdapter:
    @staticmethod
    def deserialize(data, index):
        type, h, w, value = data.split(' ')
        if type == 'R':
            return ResidentalProject(h, w, value, index)
        elif type == 'U':
            return UtilityProject(h, w, value, index)
        else:
            raise Exception('Unknown project type')


class Project:
    def __init__(self, h, w, id):
        self.h = int(h)
        self.w = int(w)
        self.plan = empty_matrix(self.h, self.w)
        self.coord = []
        self.id = id
        self.filtered_cell = []

    def found_dot(self):
        for i in range(self.h):
            for j in range(self.w):
                if self.plan[i][j] == '.' and not (i == 0 or j == 0) and not (i == self.h - 1 or j == self.w - 1):
                    return i, j

        return None, None

    def get_next_hole(self, x, y):
        right = None
        down = None
        dots = []

        if x + 1 < self.h - 1:
            down = self.plan[x + 1][y]

        if y + 1 < self.w - 1:
            right = self.plan[x][y + 1]

        if right and right == '.':
            dots = dots + [(x, y + 1)] + self.get_next_hole(x, y + 1)

        if down and down == '.':
            dots = dots + [(x + 1, y)] + self.get_next_hole(x + 1, y)

        return dots

    def is_hole_inside(self):
        i, j = self.found_dot()

        if i is None and j is None:
            return False

        dots = set([(i, j)] + self.get_next_hole(i, j))

        checks = []

        for dot in dots:

            i, j = dot

            env = []

            # right
            if j + 1 < self.w and (i, j + 1) not in dots:
                env.append(self.plan[i][j + 1])
            # left
            if j - 1 >= 0 and (i, j - 1) not in dots:
                env.append(self.plan[i][j - 1])
            # down
            if i + 1 < self.h and (i + 1, j) not in dots:
                env.append(self.plan[i + 1][j])
            # up
            if i - 1 >= 0 and (i - 1, j) not in dots:
                env.append(self.plan[i - 1][j])

            check = [True if item == '#' else False for item in env]

            checks.append(all(check))

        return all(checks) if checks else False

    def is_connected(self):
        for row in self.plan:
            horizontal_hole = [True if item == '.' else False for item in row]
            if all(horizontal_hole):
                return False

        for i in range(self.w):
            verical_hole = [True if self.plan[j][i] == '.' else False for j in range(self.h)]
            if all(verical_hole):
                return False

        if self.h == 1 or self.w == 1:
            return True

        for i in range(self.h):
            for j in range(self.w):
                if self.plan[i][j] != '#':
                    continue

                if j + 1 < self.w:
                    horizontal = self.plan[i][j + 1]
                else:
                    horizontal = self.plan[i][j - 1]

                if i + 1 < self.h:
                    vertical = self.plan[i + 1][j]
                else:
                    vertical = self.plan[i - 1][j]

                if vertical == '.' and horizontal == '.':
                    return False

        return True

    def is_left_junk_spaces(self):
        left_side_junk_spaces = [True if row[0] == '.' else False for row in self.plan]
        if all(left_side_junk_spaces):
            return True
        return False

    def is_right_junk_spaces(self):
        right_side_junk_spaces = [True if row[-1] == '.' else False for row in self.plan]
        if all(right_side_junk_spaces):
            return True
        return False

    def validate(self):
        if not self.is_connected():
            return False
        if self.is_left_junk_spaces():
            return False
        if self.is_right_junk_spaces():
            return False
        if self.is_hole_inside():
            return False

        return True


class ResidentalProject(Project):
    def __init__(self, h, w, capacity, id):
        super(ResidentalProject, self).__init__(h, w, id)
        self.capacity = int(capacity)


class UtilityProject(Project):
    def __init__(self, h, w, service, id):
        super(UtilityProject, self).__init__(h, w, id)
        self.service = int(service)


class ParseInput:
    def __call__(self, file_path, *args, **kwargs):
        with open(file_path) as _file:

            city_info = _file.readline()

            city = City.deserialize(city_info)

            for project_index in range(city.qprojects):
                project_info = _file.readline()
                project = ProjectAdapter.deserialize(project_info, project_index)

                for i in range(project.h):
                    row = _file.readline().strip()
                    j = 0
                    for item in row:

                        project.plan[i][j] = item
                        project.coord.append((i, j))

                        j = j + 1

                if project.validate():
                    city.add_project(project)

        return city


def write_res(file_path, city_plan, *args, **kwargs):
        with open(file_path, 'w+') as _file:
            res = ""

            building = city_plan.get_building_quantity()
            res += "{}\n".format(building)

            for residental_building in city_plan.residental_building:
                first_coord = residental_building.coord[0]
                res += "{} {} {}\n".format(residental_building.id, first_coord[0], first_coord[1])

            for utility_building in city_plan.utility_building:
                first_coord = utility_building.coord[0]
                res += "{} {} {}\n".format(utility_building.id, first_coord[0], first_coord[1])

            _file.write(res)


if __name__ == '__main__':

    parser = ParseInput()
    city = parser('a_example.in')
    for project in city.projects:
        print(project.plan)
    city_plan = city.construct()
    print("city value {}".format(city_plan.value))
    write_res('res.txt', city_plan)


