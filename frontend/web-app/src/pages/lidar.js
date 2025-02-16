import React, { useState, useEffect, useRef } from "react";
import "./lidar.css";
import logo from "../images/vedette_logo.png";
import ColorButton from "../components/color_button.js";
import ClientCommunicator from "@kitware/trame-iframe";
import axios from "axios";

const Lidar = () => {
  const [colorTemplate, setColorTemplate] = useState("cyan_pink");
  const [pointSize, setPointSize] = useState(3);
  const iframeRef = useRef(null);
  const [trame, setTrame] = useState(null);
  

  useEffect(() => {
    const iframe = document.getElementById("trame_app");
    if (iframe) {
      // The second argument is the 'target origin' (i.e. the domain where Trame is hosted)
      const communicator = new ClientCommunicator(iframe, "http://localhost:8080");
      setTrame(communicator);
      // communicator.on("user_data", (data) => {
      //   console.log("Received user data:", data);
      // });
      console.log(iframe);
      console.log("trying to get user data");
      communicator.trigger("get_user_data");
      console.log('done');
    }
    
    
  }, []);
  // Send color template update to backend when trame is ready
  useEffect(() => {
    if (trame) {
      // The first argument to trigger() must match the “@ctrl.trigger(...)”
      // we used in Python: "set_color_template"
      
      console.log('a');
      trame.trigger("set_color_template", colorTemplate);
      console.log('b');
    }
  }, [colorTemplate, trame]);

  function testCLick () {
    console.log("blah");
      // axios.post("http://127.0.0.1:8000/set_color_template", {
      //   template_name: "red"  // Change to red
      // })
      // .then(response => {
      //   console.log("API Response:", response.data);
      // })
      // .catch(error => {
      //   console.error("Error calling API:", error);
      // });
  }

  // Send point size update to backend when trame is ready
  useEffect(() => {
    if (trame) {
      trame.trigger("set_point_size", pointSize);
    }
  }, [pointSize, trame]);

  return (
    <div className="lidar-container">
      <div className="iframe-container">
        <iframe 
          ref={iframeRef}
          id="trame_app"
          title="Main Iframe"
          className="main-iframe"
          src="http://localhost:8080/index.html" 
          frameBorder="0"
        ></iframe>
        <div className="side-iframes">
          <iframe 
            title="Side Iframe 1"
            className="side-iframe1"
            src="https://i.ibb.co/sppB93V5/lidar-pov.png"
            frameBorder="0"
          ></iframe>
          <iframe 
            title="Side Iframe 2"
            className="side-iframe2"
            src="https://i.ibb.co/XkXR6bb7/drone-pov.png"
            frameBorder="0"
          ></iframe>
        </div>
      </div>

      <div className="bottom-sections">
        {/* Section 1 */}
        <div className="section-1">
          <div className="button-group1">
            <button className="action-button connected">▶ Launch SLAM</button>
            <button className="action-button connected">Reset SLAM</button>
          </div>
          <label className="measurement-label"> &nbsp;Measurement:</label>
          <div className="button-group2">
            <button className="action-button connected" onClick={testCLick}>[M] Add Measurement</button>
            <button className="action-button connected">[C] Clear</button>
          </div>
        </div>

        {/* Section 2 */}
        <div className="section-2">
          <label className="bottom-label"> &nbsp;Color Template:</label>
          <div id="color-button-group" className="color-button-group">
            <ColorButton colorTemplate={colorTemplate} setColorTemplate={setColorTemplate} />
          </div>

          <div className="point-settings-container">
            <div className="point-size-container">
              <label className="bottom-label"> &nbsp;Point Size:</label>
              <input
                id="slider"
                type="range"
                min="1"
                max="7"
                step="1"
                className="slider"
                value={pointSize}
                onChange={(e) => setPointSize(parseInt(e.target.value))}
              />
            </div>

            <div className="checkbox-container">
              <div className="checkbox-ambient-occlusion">
                <label>[A] Ambient Occlusion: </label>
                <input type="checkbox" /> 
              </div>
              <div className="checkbox-orthogonal-viewport">
                <label>[0] Orthogonal Viewport:</label>
                <input type="checkbox" /> 
              </div>
            </div>
          </div>
        </div>

        {/* Section 3 */}
        <div className="section-3">
          <img src={logo} className="logo" /> 
        </div>
      </div>
    </div>
  );
};

export default Lidar;
