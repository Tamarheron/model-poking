
import './App.css';
import React, { useEffect, useState } from 'react';
import { middleware } from 'yargs';



function api_call(text, temp = 0, n_tokens = 50,) {

  // send text, temperature to Flask backend
  const data = { "text": text, "temp": temp, "n_tokens": n_tokens }
  const headers = { 'Content-Type': 'application/json' }
  const args = {
    method: 'POST',
    headers: headers,
    body: JSON.stringify(data)
  }
  const completion = fetch('/submit_prompt', args).then(
    function (completion) {

      return completion.text()

    }
  )
  return completion;
  // fetch('/submit_prompt')
}


function get_completion_on_ctrl_enter(e) {
  if (e.key === 'Enter' && e.ctrlKey) {  // if enter is pressed and ctrl is held
    const button = document.getElementById("submit_prompt");
    button.click();

  }
}

async function get_logs_from_server() {
  const raw = await fetch('/get_logs')
  const logs = await raw.json()
  return logs
}

const Logs = ({ logs, remove_log_by_id, newlines }) => {

  console.log(newlines)
  var handle_save = (data) => {
    return () => {

      const headers = { 'Content-Type': 'application/json' }
      const args = {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(data)
      }
      fetch('/save_log', args)
    }
  }
  var handle_archive = (id) => {
    return () => {
      console.log('archiving ID ' + id);
      const data = { "id": id }
      const headers = { 'Content-Type': 'application/json' }
      const args = {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(data)
      }
      fetch('/archive_log', args)
      // update logs
      remove_log_by_id(id)
    }
  }

  return (
    //map over logs and display them


    logs.map((data) => {
      var prompt = data["prompt"];
      var completion = data["completion"];
      if (newlines) {
        prompt = prompt.replace(/\n/g, '<br>');
        completion = completion.replace(/\n/g, '<br>');
      };
      <tr key={data.time_id}>
        <td>
          {prompt}
        </td>
        <td>{completion}</td>
        <td>T=<br />{data.temp} <br /> <br />
          <br />  <br />
          <LogButton key={'save' + data.time_id} fun={handle_save(data)} label="save" />
          <br /> <br />
          <LogButton key={'archive' + data.time_id} fun={handle_archive(data.time_id)} label="archive" />
        </td>

      </tr>


    })
  );
}
const LogButton = (args) => {
  console.log(args);
  console.log(typeof (fun));
  return (
    <button onClick={args.fun}>{args.label}</button>
  )
}
const PromptArea = ({ update_logs, setNewlines }) => {

  const [text, setText] = useState('');
  const [temp, setTemp] = useState(0);
  const [n_tokens, setNTokens] = useState(50);


  function get_completion(text, button) {
    // make button red  to indicate that it is being pressed
    const textbox = document.getElementById("prompt_textarea");

    textbox.style.backgroundColor = "#f0f0f5";

    // send text to OpenAI API
    api_call(text, temp, n_tokens).then(completion => {
      setText(text + completion);
      textbox.style.backgroundColor = "white";
      // update logs
      console.log(typeof (update_logs))
      update_logs(text, completion, temp, n_tokens);
    });


    return
  }



  return (
    <div className='prompt_area'>
      <div className="settings_bar">
        <div className='setting'>
          <input key="temp" type="number" value={temp} onChange={(e) => setTemp(e.target.value)} />
          <label htmlFor="temp">Temp</label>
        </div>
        <div className='setting'>
          <input key="ntokens" type="number" value={n_tokens} onChange={(e) => setNTokens(e.target.value)} />
          <label htmlFor="n_tokens">NTokens</label>
        </div>
        <div className='setting'>
          <input key="change_newlines" type="checkbox" value={newlines} onChange={(e) => setNewlines(e.target.value)} />
          <label htmlFor="newlines">Show Newlines</label>
        </div>
      </div>
      <div onKeyDown={get_completion_on_ctrl_enter}>
        <textarea key="prompt_textarea" id="prompt_textarea" rows="20" value={text} onChange={(e) => setText(e.target.value)} />
        <br></br>
        <button id="submit_prompt" onClick={() => get_completion(text, temp, n_tokens)}>submit</button>
      </div>
    </div >

  );

}


function App() {
  const [logs, setLogs] = useState([]);
  const [newlines, setNewlines] = useState(false);
  useEffect(() => {
    get_logs_from_server().then(loaded_logs => {
      setLogs(loaded_logs)
    })

  }, []);
  const add_log = (text, completion, temp, n_tokens) => {
    const new_log = {
      "prompt": text,
      "completion": completion,
      "temp": temp,
      "n_tokens": n_tokens,
      "time_id": Date.now()
    }
    setLogs([new_log, ...logs])
  }
  const remove_log = (id) => {
    const new_logs = logs.filter(log => log.time_id !== id)
    setLogs(new_logs)


  }





  return (
    <div className="App">
      <PromptArea key="prompt_area" update_logs={add_log} setNewlines={setNewlines} />
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
          <tbody >
            <Logs key='logs' logs={logs} remove_log_by_id={remove_log} newlines={newlines} />
          </tbody>
        </table>
      </div>
    </div>
  );
}
export default App;

