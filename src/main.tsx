
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

console.log('Main.tsx loading...');

const rootElement = document.getElementById('root');
console.log('Root element found:', rootElement);

if (rootElement) {
  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  );
  console.log('App rendered successfully');
} else {
  console.error('Root element not found');
}
