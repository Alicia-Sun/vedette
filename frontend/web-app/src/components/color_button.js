import React, { useState } from 'react';
import './color_button.css';

const ColorButton = ({ colorTemplate, setColorTemplate }) => {
  // Handler for button click to change active color
  const handleColorClick = (color) => {
    setColorTemplate(color);
  };

  return (
    <div className="section-2">
      <div className="color-button-group">
        <button
          className={`color-button ${colorTemplate === 'cyan_pink' ? 'active' : ''}`}
          onClick={() => handleColorClick('cyan_pink')}
        >
          [1] Cyan & Pink
        </button>
        <button
          className={`color-button ${colorTemplate === 'red' ? 'active' : ''}`}
          onClick={() => handleColorClick('red')}
        >
          [2] Red
        </button>
        <button
          className={`color-button ${colorTemplate === 'blue' ? 'active' : ''}`}
          onClick={() => handleColorClick('blue')}
        >
          [3] Blue
        </button>
        <button
          className={`color-button ${colorTemplate === 'yellow' ? 'active' : ''}`}
          onClick={() => handleColorClick('yellow')}
        >
          [4] Yellow
        </button>
        <button
          className={`color-button ${colorTemplate === 'intensity' ? 'active' : ''}`}
          onClick={() => handleColorClick('intensity')}
        >
          [5] Intensity
        </button>
      </div>
    </div>
  );
};

export default ColorButton;
