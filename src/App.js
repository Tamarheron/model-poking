
import './App.css';
import React, { useEffect, useState } from 'react';



function api_call(text, temp = 0, n_tokens = 50) {
  // send text, temperature to Flask backend
  const data = { "text": text, "temp": temp, "n_tokens": n_tokens }
  const headers = { 'Content-Type': 'application/json' }
  const args = {
    method: 'POST',
    headers: headers,
    body: JSON.stringify(data)
  }
  console.log('fetching')
  const completion = fetch('/submit_prompt', args).then(
    function (completion) {
      console.log('fetching done')

      return completion.text()

    }
  )
  return completion;
  // fetch('/submit_prompt')
}


const PromptWindow = () => {

  const [text, setText] = useState('');
  const [temp, setTemp] = useState(0);
  const [n_tokens, setNTokens] = useState(50);
  function get_completion(text) {
    // send text to OpenAI API
    api_call(text, temp, n_tokens).then(completion => setText(text + completion));
    return
  }

  return (
    <div>
      <textarea rows="20" value={text} onChange={(e) => setText(e.target.value)} />
      <br></br>
      <button id="submit_prompt" onClick={() => get_completion(text, temp, n_tokens)}>submit</button>
    </div>
  )
}
const Logs = () => {
  const [logs, setLogs] = useState('');

  return (
    <tr>
      <td>
        logs
      </td>
    </tr>
  );
}
const Temp = () => {
  const [temp, setTemp] = useState(0);

  return (
    <div>
      <input type="number" value={temp} onChange={(e) => setTemp(e.target.value)} />
      <label htmlFor="temp">Temp</label>
    </div>
  );
}
const NTokens = () => {
  const [n_tokens, setNTokens] = useState(50);

  return (
    <div>
      <input type="number" value={n_tokens} onChange={(e) => setNTokens(e.target.value)} />
      <label htmlFor="n_tokens">NTokens</label>
    </div>
  );
}

const ChangeNewlines = () => {
  const [newlines, setNewlines] = useState(false);
  return (
    <div>
      <input type="checkbox" value={newlines} onChange={(e) => setNewlines(e.target.value)} />
      <label htmlFor="newlines">Show Newlines</label>
    </div>

  )
}

function get_completion_on_ctrl_enter(e) {
  if (e.key === 'Enter' && e.ctrlKey) {  // if enter is pressed and ctrl is held
    const button = document.getElementById("submit_prompt");
    button.click();

  }
}

function App() {
  return (
    <div>
      <div className="settings_bar">
        <a className='setting'>
          <Temp />
        </a>
        <a className='setting'>
          <NTokens />
        </a>
        <a className='setting'>
          <ChangeNewlines />
        </a>

      </div>
      <div onKeyDown={get_completion_on_ctrl_enter}>
        <PromptWindow />
      </div>
      <div className="container">
        <table className="logs">
          <thead>
            <tr className="table-header">

              <td>
                Prompt
              </td>
              <td>
                Completion
              </td>
              <td>
                _
              </td>
            </tr>
          </thead>
          <tbody>
            <Logs />
          </tbody>
        </table>
      </div>





    </div >

  );
}
export default App;

