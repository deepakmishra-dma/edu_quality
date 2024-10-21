const Admin = () => {
  return (
    <div>
      <div>Upload CSV</div>
      <input type="file"
             style={{
               padding: 10,
               width: "100%",
               backgroundColor: "white",
               border: "1px solid black"
             }}/>
      <div>Csv</div>
      <textarea style={{
        height: 100,
        width: "100%"
      }}/>
      <div>Template</div>
      <select style={{
        height: 30,
        paddingLeft: 10,
        width: "100%"
      }}>
        <option value="1">1</option>
        <option value="2">2</option>
        <option value="3">3</option>
        <option value="4">4</option>
        <option value="5">5</option>
      </select>
      <div>Subject</div>
      <textarea style={{
        height: 50,
        width: "100%"
      }}/>
      <div>Notice</div>
      <textarea style={{
        height: 200,
        width: "100%"
      }}/>
    </div>
  );
};

export default Admin;
