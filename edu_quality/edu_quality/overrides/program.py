import frappe 
from education.education.doctype.program.program import Program
from collections import Counter, defaultdict
import random

class customProgram(Program):
    def shuffle_divisions(self):
        academic_year = frappe.get_value(
            "Academic Year", {"custom_current_academic_year": 1}, "name"
        )
        batches = set(
            frappe.get_all(
                "Student Group",
                {"program": self.name, "academic_year": academic_year},
                pluck="batch",
            )
        )
        # get all students in the program
        students = self.get_students(academic_year)
        divisions = frappe.db.get_all('Student Group', filters={'program': self.name,'academic_year':academic_year,'disabled':0}, fields=['name','batch','max_strength'])
        allocation = self.allocate_students_to_divisions(students, divisions)
        frappe.logger('allocation').exception(allocation)
        return allocation
        

    def allocate_students_to_divisions(self, students, divisions):
        # Group divisions by batch
        divisions_by_batch = defaultdict(list)
        for division in divisions:
            divisions_by_batch[division['batch']].append(division)
        
        # Group students by batch, house, and gender
        students_by_batch = defaultdict(lambda: defaultdict(list))
        for student in students:
            students_by_batch[student['batch']][(student['house'], student['gender'])].append(student)
        
        # Shuffle students within each house-gender group to ensure randomness
        for batch in students_by_batch:
            for group in students_by_batch[batch]:
                random.shuffle(students_by_batch[batch][group])
        
        # Allocate students to divisions
        division_allocation = defaultdict(list)
        for batch, batch_students in students_by_batch.items():
            if batch not in divisions_by_batch:
                raise ValueError(f"No divisions available for batch {batch}")
            
            division_list = divisions_by_batch[batch]
            division_count = len(division_list)
            division_indices = {division['name']: 0 for division in division_list}

            for group, students_in_group in batch_students.items():
                division_index = 0
                for student in students_in_group:
                    while division_indices[division_list[division_index]['name']] >= division_list[division_index]['max_strength']:
                        division_index = (division_index + 1) % division_count
                    
                    division_allocation[division_list[division_index]['name']].append(student)
                    division_indices[division_list[division_index]['name']] += 1
                    division_index = (division_index + 1) % division_count

        return division_allocation



    def get_students(self,academic_year):
        return frappe.db.sql(
            """
            SELECT s.name, s.first_name, s.gender, p.name as pname, p.school_house as house, d.batch
            FROM `tabStudent` as s
            LEFT JOIN `tabProgram Enrollment` as p
            ON s.name = p.student
            LEFT JOIN `tabStudent Group` as d
            ON p.student_group = d.name
            WHERE p.program = %s and p.academic_year = %s and s.student_status != 'Cancelled' 
            GROUP BY d.batch, p.school_house, s.gender, s.name
            ORDER BY d.batch, p.school_house, s.gender, RAND()
            """,
            (self.name, academic_year),
            as_dict=True,
        )