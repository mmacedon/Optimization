import sys

from crossword import *
import queue

class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for var in self.crossword.variables:
            domain = self.domains[var].copy()
            for word in self.domains[var]:
                if len(word) != var.length:
                    domain.remove(word)
            self.domains[var] = domain.copy()

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        revised = False
        count = 0
        #print(x, y)
        domainX = self.domains[x].copy()
        domainY = self.domains[y]
        overlap = self.crossword.overlaps[x, y]
        overlapX, overlapY = overlap[0], overlap[1]
        #print("OverLap", overlapX, overlapY, overlap)
        if overlap == None:
            return revised

        for wordX in self.domains[x]:
            count = 0
            for wordY in self.domains[y]:
                #print(wordX, wordY, domainX, domainY)
                if wordX == wordY: continue
                if wordX[overlapX] != wordY[overlapY]:
                    #print("OverlapLetterX: ", wordX[overlapX], "OverlapLetterY:", wordY[overlapY])
                    revised = True
                    count += 1
            if count == len(self.domains[y]):
                #print(wordX, " does not satisfy constraint... removing\n")
                domainX.remove(wordX)


        self.domains[x] = domainX.copy()

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        if arcs == None:
            q = queue.Queue()
            #Get a list of all the arcs in the problem
            for var in self.crossword.variables:
                neighbors = self.crossword.neighbors(var)
                for neighbor in neighbors:
                    q.put((var, neighbor))
                #print(var)
                #print("Neighbors:")
                #for neighbor in neighbors:
                #    print(neighbor)
                #print("End---")

        while not q.empty():
            x, y = q.get()
            if self.revise(x, y):
                if len(self.domains[x]) == 0:
                    return False
                for z in (self.crossword.neighbors(x) - y):
                    q.put(z, x)

        return True if self.domains[x] != 0 and self.domains[y] != 0 else False

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        complete = True
        for var in self.crossword.variables:
            if var not in assignment or assignment[var] == None:
                complete = False
        return complete

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        consistent = True
        for var in assignment:
            #print("=====ASSIGNMENT====")
            #print(assignment)
            if len(assignment[var]) != var.length: #Check Length
                #print("LENGTH CHECKS OUT")
                consistent = False
            for var2 in assignment:
                if var == var2: continue
                if assignment[var] == assignment[var2]: #Check if another assignment mapped to same word
                    consistent = False
            neighbors = self.crossword.neighbors(var)
            for neighbor in neighbors: #Check if neighboring words do not match with current word
                if neighbor not in assignment: continue
                overlap = self.crossword.overlaps[var, neighbor]
                #print(overlap)
                overlapX, overlapY = overlap[0], overlap[1]
                if assignment[var][overlapX] != assignment[neighbor][overlapY]:
                    consistent = False

        return consistent

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        if len(assignment) == 0:
            return self.domains[var]

        domainvaluesX = self.domains[var]
        neighbors = self.crossword.neighbors(var)
        count = 0
        min_count = float('inf')
        smallest_domain = None
        for neighbor in neighbors:
            if neighbor in assignment:
                continue
            overlaps = self.crossword.overlaps[var, neighbor]
            if overlaps == None:
                continue
            domainvaluesY = self.domains[neighbor]
            for domainvalue in domainvaluesX:
                if domainvalue in domainvaluesY:
                    count += 1
                if count < min_count:
                    min_count = count
                    smallest_domain = domainvaluesX
        return smallest_domain if smallest_domain != None else self.domains[var]

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        smallest_domain = float('inf')
        smallest_variable = None
        for var in self.crossword.variables:
            if var not in assignment:
                if len(self.domains[var]) < smallest_domain:
                    smallest_variable = var
                    smallest_domain = len(self.domains[var])
        return smallest_variable

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if (self.assignment_complete(assignment)):
            #print("Assignment Complete. Returning...")
            return assignment

        var = self.select_unassigned_variable(assignment)
        for value in self.order_domain_values(var, assignment):
            assignment[var] = value
            if self.consistent(assignment):
                #print("Consistent")
                result = self.backtrack(assignment)
                if result != None:
                    return result
            del assignment[var]



def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
