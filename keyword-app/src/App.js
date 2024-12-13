import React from 'react';
import './App.css';
import KeywordSuggestion from './KeywordSuggestion';
import Logo from './Staffs-Logo.png';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <img src={Logo} className="App-logo" alt="Staffordshire University Logo" />
      </header>
      <div className="container">
        <KeywordSuggestion />
      </div>
    </div>
  );
}

export default App;
