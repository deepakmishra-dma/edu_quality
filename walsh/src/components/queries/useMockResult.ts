const useMockResult = () => {
  return {
    subjects: [
      {
        name: "English",
        result: [{ term1: 99, term2: 99, grade: "A+", gradePoints: "10/10" }],
      },
      {
        name: "Social Studies",
        result: [{ term1: 99, term2: 99, grade: "A+", gradePoints: "10/10" }],
      },
      {
        name: "Economics",
        result: [{ term1: 99, term2: 99, grade: "A+", gradePoints: "10/10" }],
      },
      {
        name: "Science",
        result: [{ term1: 99, term2: 99, grade: "A+", gradePoints: "10/10" }],
      },
    ],
    remarks:
      "It has been truly inspiring to witness your growth this term. Your dedication to improving in areas that previously challenged you has paid off, demonstrating that perseverance is a key to overcoming obstacles.",
    attendance: [
      {
        attendance: "Term 1",
        attended: "98",
        total: 100,
        percentage: "98%",
      },
    ],
    result: "Good Passed",
  };
};

export default useMockResult;
