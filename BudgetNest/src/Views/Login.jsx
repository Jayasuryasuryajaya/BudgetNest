import React from "react";
import "bootstrap/dist/css/bootstrap.min.css";  
import "bootstrap-icons/font/bootstrap-icons.css";
import {toast}from 'react-toastify'
import { useFormik } from "formik";
import * as Yup from "yup";
const Login = () => {
  const formik = useFormik({
    initialValues: {
      username: "",
      password: "",
    },
    validationSchema: Yup.object({
      username: Yup.string()
        .min(8, "Username must be at least 8 characters")
        .required("Username is required"),
      password: Yup.string()
        .min(6, "Password must be at least 6 characters")
        .required("Password is required"),
    }),
    onSubmit: (values, { setSubmitting }) => {
     toast.success('Logined Successfully!',{position:'top-center'});
     console.log(values)
     setSubmitting(false)
    },
  });

  return (
    <section className="container-fluid m-0 p-0 d-flex overflow-hidden ">
     <section className='card rounded d-flex ms-3 mt-5 me-3 flex-row justify-content-center align-items-center'>
      <section className="col-md-6 p-5 ">
        <h1 className="text-dark">Take Control of Your Finances</h1>
        <p className="text-center w-75">
          Manage your expenses effortlessly with BudgetNest, the smart way to track your income and spending.
          Stay organized, eliminate unnecessary expenses, and make every rupee count.
        </p>
      </section>
      <section className="col-md-6 d-flex flex-column justify-content-center align-items-center text-white p-5" style={{ backgroundColor: "black" }}>
        <h2>Login to Your Account</h2>

        <form className="w-75 mt-4" onSubmit={formik.handleSubmit}>
          
          <div className="input-group mb-3">
            <span className="input-group-text"><i className="bi bi-person"></i></span>
            <input
              type="text"
              name="username"
              placeholder="Username"
              className="form-control"
              value={formik.values.username}
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
            />
          </div>
          {formik.touched.username && formik.errors.username && (
            <div className="text-danger mb-2">{formik.errors.username}</div>
          )}

         
          <div className="input-group mb-3">
            <span className="input-group-text"><i className="bi bi-lock"></i></span>
            <input
              type="password"
              name="password"
              placeholder="Password"
              className="form-control"
              value={formik.values.password}
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
            />
          </div>
          {formik.touched.password && formik.errors.password && (
            <div className="text-danger mb-2">{formik.errors.password}</div>
          )}

          <button type="submit" className="btn btn-warning w-100">
            LOGIN <i className="bi bi-box-arrow-in-right"></i>
          </button>

          
          <p className="text-center mt-3">
            <a href="#" className="text-white text-decoration-underline">
              Forgot password? <i className="bi bi-question-circle"></i>
            </a>
          </p>
        </form>
      </section>
      </section>
    </section>
  );
};

export default Login;
