
import './App.css';
import React, { useEffect, useState } from 'react';
import axios from 'axios'


function api_call(text) {
  // send text to OpenAI API using fetch
  const url = "https://api.openai.com/v1/engines/rust/completion";
  const params = {
    "engine": "davinci-text-002",
    "text": text,
    "max_choices": 10,
    "temperature": 0.8,
  }

  const response = fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": "Bearer " + process.env.REACT_APP_OPENAI_API_KEY,
    },
    body: JSON.stringify(params),
  });


  return " API completion";
}

const Prompt_Window = () => {

  const [text, setText] = useState('');
  function get_completion(text) {
    // send text to OpenAI API
    var completion = api_call(text);
    setText(text + completion);
    return
  }

  return (
    <div>
      <textarea rows="20" value={text} onChange={(e) => setText(e.target.value)} />
      <br></br>
      <button id="submit_prompt" onClick={() => get_completion(text)}>submit</button>
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
  useEffect(() => {
    axios.get('http://localhost:5002/flask/hello').then(response => {
      console.log("SUCCESS", response)
      setGetMessage(response)
    }).catch(error => {
      console.log(error)
    })

  }, [])
  return (
    <div onKeyDown={get_completion_on_ctrl_enter}>
      <Prompt_Window />
    </div>
  );
}

export default App;
