import React,{lazy,Suspense} from 'react'
import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap-icons/font/bootstrap-icons.css";
import { ToastContainer } from "react-toastify";
import {BrowserRouter,Routes,Route} from 'react-router-dom'
const Login = React.lazy(()=>import('./Views/Login.jsx'));
const Dashboard = React.lazy(()=>import('./Views/Dashboard/Dashboard.jsx'));
const NavBar =  React.lazy(()=>import('./Views/NavBar.jsx'));
const Progress =React.lazy(()=>import('./Views/Dashboard/Progress.jsx')) ;
const App = () => {
  return (
    <div className='m-0 container-fluid p-0'>
      <Suspense fallback={
        <section style={{minHeight:'100vh'}} className='fw-2 fs-5 d-flex justify-content-center align-items-center'>Loading....</section>
      }>
      <BrowserRouter>
      <NavBar />
      <Routes>
        <Route path='/' element={<Dashboard/>} />
        <Route path='/Progress'  element={<Progress/>} />
        <Route path='/Login'  element={<Login/>} />
      </Routes>
  </BrowserRouter>
  <ToastContainer />
      </Suspense>
    
    </div>
  )
}

export default App
