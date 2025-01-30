import React from 'react';
import './lidar.css';
import logo from '../images/vedette_logo.png';



const Lidar = () => (
  <div className="lidar-container">
    <div className="iframe-container">
      <iframe 
        title="Main Iframe"
        className="main-iframe"
        src="https://www.example.com"
        frameBorder="0"
      ></iframe>
      <div className="side-iframes">
        <iframe 
          title="Side Iframe 1"
          className="side-iframe1"
          src="https://www.example.com"
          frameBorder="0"
        ></iframe>
        <iframe 
          title="Side Iframe 2"
          className="side-iframe2"
          src="https://www.example.com"
          frameBorder="0"
        ></iframe>
      </div>
    </div>
    <div className="bottom-sections">
      {/* Section 1 */}
      <div className="section-1">
        <div className="button-group1">
          <button className="action-button connected" >▶ Launch SLAM</button>
          <button className="action-button connected">Reset SLAM</button>
        </div>
        <label className="measurement-label"> &nbsp;Measurement:</label>
        <div className="button-group2">
          <button className="action-button connected">[M] Add Measurement</button>
          <button className="action-button connected">[C] Clear</button>
        </div>
      </div>

      {/* Section 2 */}
      <div className="section-2">
        <label class="bottom-label"> &nbsp;Color Template:</label>
        <div className="color-button-group">
          <button className="color-button first">[1] Cyan & Pink</button>
          <button className="color-button">[2] Red</button>
          <button className="color-button">[3] Blue</button>
          <button className="color-button">[4] Yellow</button>
          <button className="color-button last">[5] Intensity</button>
        </div>

        <div className="point-settings-container">
          <div className="point-size-container">
            <label className="bottom-label"> &nbsp;Point Size:</label>
            <input type="range" min="1" max="7" step="1" className="slider" />
          </div>

          <div className="checkbox-container">
            <div className="checkbox-ambient-occlusion">
              <label>[A] Ambient Occlusion: </label>
              <label>
                <input type="checkbox"/> 
              </label>
            </div>
            <div className="checkbox-orthogonal-viewport">
              <label>[0] Orthogonal Viewport:</label>
              <label>
                <input type="checkbox"/> 
              </label>
            </div>
          </div>
        </div>
      </div>


      {/* Section 3 */}
      <div className="section-3">
        <img 
            src={logo}
            className="logo" 
        /> 
      </div>
    </div>
  </div>
);

export default Lidar;
