import React, { useState } from 'react';
import './color_button.css';

const ColorButton = () => {
  // State to track the active button
  const [activeColor, setActiveColor] = useState(null);

  // Handler for button click to change active color
  const handleColorClick = (color) => {
    setActiveColor(color);
  };

  return (
    <div className="section-2">
      <div className="color-button-group">
        <button
          className={`color-button ${activeColor === 'cyan' ? 'active' : ''}`}
          onClick={() => handleColorClick('cyan')}
        >
          [1] Cyan & Pink
        </button>
        <button
          className={`color-button ${activeColor === 'red' ? 'active' : ''}`}
          onClick={() => handleColorClick('red')}
        >
          [2] Red
        </button>
        <button
          className={`color-button ${activeColor === 'blue' ? 'active' : ''}`}
          onClick={() => handleColorClick('blue')}
        >
          [3] Blue
        </button>
        <button
          className={`color-button ${activeColor === 'yellow' ? 'active' : ''}`}
          onClick={() => handleColorClick('yellow')}
        >
          [4] Yellow
        </button>
        <button
          className={`color-button ${activeColor === 'intensity' ? 'active' : ''}`}
          onClick={() => handleColorClick('intensity')}
        >
          [5] Intensity
        </button>
      </div>
    </div>
  );
};

export default ColorButton;
