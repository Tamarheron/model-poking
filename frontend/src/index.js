import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import { Auth0Provider } from "@auth0/auth0-react";

const root = ReactDOM.createRoot(document.getElementById('root'));
//get enviroment variables from flask server

console.log(window.location.origin);

root.render(
  <Auth0Provider
    domain='wandering-sky-2847.us.auth0.com'
    clientId='PsieF7RiNvIPSRbH4tB9N3dnrAqfFScm'
    redirectUri='https://model-poking-2.herokuapp.com/'
  >
    <React.StrictMode>
      <App />
    </React.StrictMode>
  </Auth0Provider>,
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
