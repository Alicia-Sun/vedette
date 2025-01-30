import React, { useState } from 'react';
import './slider.css'

const SliderComponent = () => {
  const [value, setValue] = useState(1);  // initial value of the slider

  const handleSliderChange = (e) => {
    setValue(e.target.value);
  };

  return (
    <div className="slider-container">
      <input
        type="range"
        min="1"
        max="7"
        step="1"
        value={value}
        onChange={handleSliderChange}
        className="slider"
        style={{
          background: `linear-gradient(to right, #d81b60 ${((value - 1) / 6) * 100}%, #f1b4be 0%)`,
        }}
      />
    </div>
  );
};

export default SliderComponent;
