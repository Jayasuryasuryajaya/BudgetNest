import React from "react";
import { Navbar, Nav, Container, Button } from "react-bootstrap";
import { Link } from "react-router-dom";

const NavBar = () => {
  return (
    <div className='container-fluid m-0 p-0' >
    <Navbar expand="lg"  variant="dark" style={{backgroundColor:'black'}}>
      <Container >
        <Navbar.Brand as={Link} to="/" className='fs-2' > <img src="../public/icon.jpg" className='rounded-circle' width='70' height='70' /> BudgetNest </Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className='ms-auto'>
            <Nav.Link as={Link} to="/">Home</Nav.Link>
            <Nav.Link as={Link} to="/">Add Expense</Nav.Link>
            <Nav.Link as={Link} to="/">Invest</Nav.Link>
            <Nav.Link as={Link} to="/">Goals & Savings </Nav.Link>
            <Nav.Link as={Link} to="/">History </Nav.Link>
            <Nav.Link as={Link} to="/">Help & Support</Nav.Link>
            <Nav.Link as={Link} to="/Login">
              <Button variant="light" className="text-dark rounded-pill px-5">Sign Up</Button>
            </Nav.Link>
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
    </div>
  );
};

export default NavBar;
