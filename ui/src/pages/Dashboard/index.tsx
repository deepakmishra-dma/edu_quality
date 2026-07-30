// import { HomeIcon } from "lucide-react";
import { Outlet } from "react-router-dom";

function Home() {
  return (
    <div className="flex flex-col justify-center items-center bg-gray-50">
      {/* <Link
        to="/"
        className="max-w-xs w-full flex justify-center items-center px-6 py-3 bg-blue-500 text-white font-semibold rounded-lg hover:bg-blue-600 transition duration-200 mt-2"
      >
        <HomeIcon className="mr-2" />
        Home
      </Link> */}
      <Outlet />
    </div>
  );
}

export default Home;
