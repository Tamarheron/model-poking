
import './App.css';
import React, { useEffect, useState } from 'react';



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
async function get_logprobs(data) {
  // send text, temperature to Flask backend
  const headers = { 'Content-Type': 'application/json' }
  const args = {
    method: 'POST',
    headers: headers,
    body: JSON.stringify(data)
  }
  const response = fetch('/get_answer', args).then(
    function (response) {
      const logprobs = response.json()
      console.log('get_logprobs, answer: ' + logprobs);
      return logprobs
    }
  )
  return response;
  // return { '0': 0.5, '1': 0.5 };
}

function handle_prompt_keypress(e) {
  if (e.key === 'Enter' && e.ctrlKey) {  // if enter is pressed and ctrl is held
    const button = document.getElementById("submit_prompt");
    button.click();

  } else if (e.key === 'ArrowDown' && e.ctrlKey) {
    //move focus to option area
    const option_area = document.getElementById("option_textarea");
    option_area.focus();
  }
}
function handle_option_keypress(e) {
  if (e.key === 'Enter' && !e.ctrlKey) {  // if enter is pressed and ctrl is held
    // stop default behavior
    e.preventDefault();
    const button = document.getElementById("submit_option");

    button.click();

  } else if (e.key === 'ArrowUp' && e.ctrlKey) {
    //move focus to option area
    const option_area = document.getElementById("prompt_textarea");
    option_area.focus();
  }
}

async function get_logs_from_server() {
  const raw = await fetch('/get_logs')
  const logs = await raw.json()
  return logs
}

const Logs = ({ logs, remove_log_by_id, white_space_style }) => {
  // console.log(JSON.parse(logs[0]));
  // console.log(logs[0]["prompt"]);
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
  var logs_to_display = logs.map((log) => {
    return log
  });

  const jsx = logs_to_display.map((data) =>
    // const prompt = data["prompt"];
    // const completion = data["completion"];

    // if (newlines) {
    //   prompt = prompt.replace(/\n/g, '<br>');
    //   completion = completion.replace(/\n/g, '<br>');
    // };

    <tr key={data.time_id} style={{ whiteSpace: white_space_style }}>
      <td>
        {data.prompt}
      </td>
      <td>{data.completion}</td>
      <td>T=<br />{data.temp} <br /> <br />
        <br />  <br />
        <LogButton key={'save' + data.time_id} fun={handle_save(data)} label="save" />
        <br /> <br />
        <LogButton key={'archive' + data.time_id} fun={handle_archive(data.time_id)} label="archive" />
      </td>

    </tr>

  );
  console.log('jsx ' + jsx);
  return (jsx);
}

const LogButton = (args) => {
  return (
    <button onClick={args.fun}>{args.label}</button>
  )
}
function parse_options(text) {

  const option_text = String(text.split('Options:\n').slice(-1))
  const option_lines = option_text.split('\n');
  const options = option_lines.map((option_line) => {
    return option_line.slice(2,);
  });
  console.log('parsed options ' + options);
  return options;
}

const OptionsAnswersList = ({ option_list, get_answers }) => {
  console.log('OAL, options: ' + option_list);

  const [answers, setAnswers] = useState([]);

  useEffect(() => {
    console.log('useEffect, options: ' + option_list);

    const fetchAnswers = async () => {
      const answers = await get_answers();
      setAnswers(answers);
      console.log('fetchanswers: ' + answers);
      console.log(answers)

    }
    if (option_list.length > 1) {
      fetchAnswers();
    }
  }, []);

  console.log('OAL2, options: ', option_list, typeof option_list, option_list.length);


  var display_answers = [];
  if (answers !== undefined) {
    display_answers = answers.map((answer) => {
      return answer
    });
  }
  const logprobs = option_list.map((_, i) => {
    if (display_answers[i] !== undefined) {
      return display_answers[i];
    } else {
      return 'None';
    }
  }
  )
  var jsx = '';
  if (option_list.length > 0) {
    jsx = option_list.map((option, index) =>
      <tr key={index}>
        <td>{index + 1 + ') '}{option} </td>
        <td>{logprobs[index]}</td>
      </tr>
    );
  }
  console.log('jsx ' + jsx);
  return (jsx);
}


const PromptArea = ({ update_logs, newlines, set_newlines }) => {

  const [text, setText] = useState('');
  const [temp, setTemp] = useState(0);
  const [n_tokens, setNTokens] = useState(50);
  const [option_text, setOptionText] = useState('');
  const [setting, setSetting] = useState('You are an AI. What do you want to say?');
  const [show_setting, setShowSetting] = useState(false);
  const [options, setOptions] = useState([]);
  console.log('promptare options1: ' + options);

  function get_completion() {
    const textbox = document.getElementById("prompt_textarea");
    textbox.style.backgroundColor = "#f0f0f5";

    // send text to OpenAI API
    api_call(setting + text, temp, n_tokens).then(completion => {
      setText(text + completion);
      textbox.style.backgroundColor = "white";
      // update logs
      update_logs(text, completion, temp, n_tokens);
    });


    return
  }
  function submit_option() {
    // check if last line of text starts with a number
    const last_line = text.split('\n').pop();
    const last_line_first = last_line[0];
    var start = "\nOptions:\n1) ";
    if (last_line_first) {
      if (last_line_first.match(/^\d+$/)) {
        // add option to last line
        const current_num = parseInt(last_line_first);
        start = '\n' + String(current_num + 1) + ") ";
      }
    }
    setText(text + start + option_text);
    if (option_text.slice(-1) === '\n') {
      option_text = option_text.slice(0, -1);
    }
    console.log(': ' + option_text);
    console.log('old options: ' + options);
    const new_options = [...options, option_text];
    setOptions(new_options);
    console.log('set_options: ' + options);
    setOptionText('');
  }
  console.log('promptare options2: ' + options);
  console.log(options)

  async function get_answers() {
    const prompt = setting + text + '\n> The best action is option';
    //interaction is everything up to last 'option'
    const interaction = text.split('Options:\n').slice(0, -1).join('Options:\n');
    const data = { "prompt": prompt, 'setting': setting, 'interaction': interaction, 'options': options }
    //get list of logprobs
    const logprobs = await get_logprobs(data);
    console.log('get_answers returnning logprobs: ' + logprobs);
    console.log(logprobs);

    return logprobs;

  };



  function handle_text_change(new_text) {
    console.log('handle_text_change, new_text ' + new_text);
    setText(new_text);
    if (new_text !== '') {
      const new_options = parse_options(new_text);
      console.log('handle text new_options: ' + new_options);
      if (new_options !== options) {
        setOptions(new_options);
      }
    }
  }

  const SettingBox = () => {
    if (show_setting) {
      return (
        <div >
          <textarea key="setting_textarea" id="setting_textarea" rows="20" value={setting} onChange={(e) => setSetting(e.target.value)} />
          <br></br>
        </div>
      )
    } else {
      return (
        <div >

        </div>
      )
    }
  }


  console.log('promptare options: ' + options);
  return (
    <div key='prompt_area' className='prompt_area'>
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
          <input key="change_newlines" type="checkbox" value={newlines} onChange={(e) => set_newlines(!newlines)} />
          <label htmlFor="newlines">Show Newlines</label>
        </div>
        <div className='setting'>
          <input key="change_show_setting" type="checkbox" value={show_setting} onChange={(e) => setShowSetting(!show_setting)} />
          <label htmlFor="newlines">Show Setting</label>
        </div>
      </div>
      {SettingBox()}
      <div onKeyDown={handle_prompt_keypress}>
        <textarea key="prompt_textarea" id="prompt_textarea" rows="20" value={text} onChange={(e) => handle_text_change(e.target.value)} />
        <br></br>
        <button id="submit_prompt" onClick={() => get_completion()}>get completion</button>
      </div>
      <div onKeyDown={handle_option_keypress}>
        <textarea key="option_textarea" id="option_textarea" rows="1" value={option_text} onChange={(e) => setOptionText(e.target.value)} />
        <br></br>
        <button id="submit_option" onClick={() => submit_option()}>add option</button>
      </div>
      <div>
        <table>
          <tbody>
            <OptionsAnswersList option_list={options} get_answers={() => get_answers()} />
          </tbody>
        </table>
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
  const set_newlines = (newlines) => {
    setNewlines(newlines)
  }
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
  console.log(newlines);
  var white_space_style = 'normal'
  if (newlines) {
    white_space_style = 'pre-line'
  }

  return (
    <div className="App">
      <PromptArea key="prompt_area" update_logs={add_log} newlines={newlines} set_newlines={set_newlines} />
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
            <Logs key='logs' logs={logs} remove_log_by_id={remove_log} white_space_style={white_space_style} />
          </tbody>
        </table>
      </div>
    </div>
  );
}
export default App;

