import React, { useState, useEffect, useRef } from "react";
import "./lidar.css";
import logo from "../images/vedette_logo.png";
import ColorButton from "../components/color_button.js";
import { TrameIframeApp } from '@kitware/trame-react';

// inspired by trame-react examples
function debounce(func, wait) {
  let timeout;

  return function (...args) {
    const context = this;

    clearTimeout(timeout); // Clears the previous timeout
    timeout = setTimeout(() => func.apply(context, args), wait); // Sets a new timeout
  };
}

function deepEqual(obj1, obj2) {
  if (obj1 === obj2) return true;
  if (
    typeof obj1 !== 'object' ||
    obj1 === null ||
    typeof obj2 !== 'object' ||
    obj2 === null
  )
    return false;

  const keys1 = Object.keys(obj1);
  const keys2 = Object.keys(obj2);

  if (keys1.length !== keys2.length) return false;

  for (let key of keys1) {
    if (!keys2.includes(key) || !deepEqual(obj1[key], obj2[key])) {
      return false;
    }
  }

  return true;
}

function stateIsSync(localState, trameState) {
  const localStateKeys = Object.keys(localState);
  const trameStatekeys = Object.keys(trameState);

  for (let localKey of localStateKeys) {
    if (
      !trameStatekeys.includes(localKey) ||
      !deepEqual(localState[localKey], trameState[localKey])
    ) {
      return false;
    }
  }

  return true;
}

const Lidar = () => {
  const [viewerState, setViewerState] = useState({
    color_template: "cyan_pink",
    point_size: 3,
    slam_status: false,
  });
  // const trameCommunicator = useRef(null);
  const trameCommunicatorMain = useRef(null); // For localhost:8080
  const trameCommunicatorPOV = useRef(null); // For localhost:9000
  const synchronizeTrameState = useRef(null);

  // const startSLAM = () => {
  //   if (!trameCommunicator.current) return;
  //   trameCommunicator.current.state.update({ slam_status: !viewerState.slam_status }); // Set state.slam to "start"
  //   console.log("Toggling Slam status")
  // };  
  const startSLAM = () => {
    if (trameCommunicatorMain.current) {
      trameCommunicatorMain.current.state.update({ slam_status: !viewerState.slam_status });
    }
    if (trameCommunicatorPOV.current) {
      trameCommunicatorPOV.current.state.update({ slam_status: !viewerState.slam_status });
    }
    console.log("Toggling Slam status");
  };

  // useEffect(() => {
  //   synchronizeTrameState.current = debounce((viewerState) => {
  //     if (!trameCommunicator.current) {
  //       return;
  //     }

  //     trameCommunicator.current.state.get().then((trame_state) => {
  //       if (!stateIsSync(viewerState, trame_state)) {
  //         trameCommunicator.current.state.update(viewerState);
  //       }
  //     });
  //   }, 25);
  // }, []);
  useEffect(() => {
    synchronizeTrameState.current = debounce((viewerState) => {
      if (trameCommunicatorMain.current) {
        trameCommunicatorMain.current.state.get().then((trame_state) => {
          if (!stateIsSync(viewerState, trame_state)) {
            trameCommunicatorMain.current.state.update(viewerState);
          }
        });
      }
      if (trameCommunicatorPOV.current) {
        trameCommunicatorPOV.current.state.get().then((trame_state) => {
          if (!stateIsSync(viewerState, trame_state)) {
            trameCommunicatorPOV.current.state.update(viewerState);
          }
        });
      }
    }, 25);
  }, []);
  

  useEffect(() => {
    synchronizeTrameState.current(viewerState);
  }, [viewerState]);
  

  // const onViewerReady = (comm) => {
  //   trameCommunicator.current = comm;

  //   trameCommunicator.current.state.onReady(() => {
  //     trameCommunicator.current.state.watch(
  //       ['point_size'],
  //       (point_size) => {
  //         console.log({ point_size });
  //       }
  //     );
  //     trameCommunicator.current.state.watch(
  //       ['color_template'],
  //       (color_template) => {
  //         console.log({ color_template });
  //       }
  //     );
  //     trameCommunicator.current.state.watch(
  //       ['slam_status'],
  //       (slam_status) => {
  //         console.log({ slam_status });
  //       }
  //     );

  //     trameCommunicator.current.state.watch(
  //       ['color_template', 'point_size', 'slam_status'],
  //       (color_template, point_size, slam_status) => {
  //         setViewerState((prevState) => ({
  //           ...prevState,
  //           color_template: color_template ?? "cyan_pink",
  //           point_size: point_size ?? 3,
  //           slam_status: slam_status ?? false,
  //         }));
  //       }
  //     );
  //   });
  // };
  const onViewerReadyMain = (comm) => {
    trameCommunicatorMain.current = comm;
    setupCommunicator(comm);
  };
  
  const onViewerReadyPOV = (comm) => {
    trameCommunicatorPOV.current = comm;
    setupCommunicator(comm);
  };
  
  const setupCommunicator = (comm) => {
    comm.state.onReady(() => {
      comm.state.watch(['point_size'], (point_size) => {
        console.log({ point_size });
      });
      comm.state.watch(['color_template'], (color_template) => {
        console.log({ color_template });
      });
      comm.state.watch(['slam_status'], (slam_status) => {
        console.log({ slam_status });
      });
  
      comm.state.watch(
        ['color_template', 'point_size', 'slam_status'],
        (color_template, point_size, slam_status) => {
          setViewerState((prevState) => ({
            ...prevState,
            color_template: color_template ?? "cyan_pink",
            point_size: point_size ?? 3,
            slam_status: slam_status ?? false,
          }));
        }
      );
    });
  };

  return (
    <div className="lidar-container">
      <div className="iframe-container">
        <div className="main-iframe">
          <TrameIframeApp
            iframeId={"trame_app"}
            url={"http://localhost:8080/index.html"}
            onCommunicatorReady={onViewerReadyMain}
          />
        </div>
        <div className="side-iframes">
          {/* <iframe 
            title="Side Iframe 1"
            className="side-iframe1"
            src="http://localhost:9000/index.html"
            frameBorder="0"
          ></iframe> */}
          <TrameIframeApp
            iframeId={"lidar_pov"}
            url={"http://localhost:9000/index.html"}
            onCommunicatorReady={onViewerReadyPOV}
          />
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
            <button className="action-button connected" 
            onClick= {startSLAM}>▶ Launch SLAM</button>
            <button className="action-button connected">Reset SLAM</button>
          </div>
          <label className="measurement-label"> &nbsp;Measurement:</label>
          <div className="button-group2">
            <button className="action-button connected" >[M] Add Measurement</button>
            <button className="action-button connected">[C] Clear</button>
          </div>
        </div>

        {/* Section 2 */}
        <div className="section-2">
          <label className="bottom-label"> &nbsp;Color Template:</label>
          <div id="color-button-group" className="color-button-group">
            <ColorButton color_template={viewerState.color_template} 
              setColorTemplate={(color) => {
                setViewerState((prevViewerState) => ({
                  ...prevViewerState,
                  color_template: color,
                }));
              }}
            /> 
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
                value={viewerState.point_size || 3}
                onChange={(e) => {
                  setViewerState((prevViewerState) => ({
                    ...prevViewerState,
                    point_size: parseInt(e.target.value, 10) || 3,
                  }));
                }}
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
          <img src={logo} className="logo" alt="vedette_logo"/> 
        </div>
      </div>
    </div>
  );
};

export default Lidar;