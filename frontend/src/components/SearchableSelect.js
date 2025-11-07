import React, { useState, useEffect, useRef } from 'react';

function SearchableSelect({ value, onChange, options, placeholder, label }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [filteredOptions, setFilteredOptions] = useState(options);
  const dropdownRef = useRef(null);

  useEffect(() => {
    // Filter options based on search term
    if (searchTerm) {
      const filtered = options.filter(option =>
        option.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        option.team.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredOptions(filtered);
    } else {
      setFilteredOptions(options);
    }
  }, [searchTerm, options]);

  useEffect(() => {
    // Close dropdown when clicking outside
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (option) => {
    onChange(option.name);
    setSearchTerm('');
    setIsOpen(false);
  };

  const handleInputChange = (e) => {
    setSearchTerm(e.target.value);
    setIsOpen(true);
  };

  const handleInputFocus = () => {
    setIsOpen(true);
  };

  // Get display value
  const selectedOption = options.find(opt => opt.name === value);
  const displayText = selectedOption
    ? `${selectedOption.name} (${selectedOption.team}${selectedOption.position ? ' - ' + selectedOption.position : ''})`
    : '';

  return (
    <div ref={dropdownRef} className="relative">
      <label className="block text-sm font-medium mb-2">{label}</label>
      <div className="relative">
        <input
          type="text"
          value={isOpen ? searchTerm : displayText}
          onChange={handleInputChange}
          onFocus={handleInputFocus}
          placeholder={placeholder}
          className="w-full p-3 rounded-lg bg-white/20 text-white border border-white/30 focus:outline-none focus:ring-2 focus:ring-orange-500 placeholder-gray-400"
          autoComplete="off"
        />

        {isOpen && filteredOptions.length > 0 && (
          <div className="absolute z-50 w-full mt-1 max-h-64 overflow-y-auto bg-gray-800 border border-gray-600 rounded-lg shadow-xl">
            {filteredOptions.slice(0, 100).map((option) => (
              <div
                key={option.id}
                onClick={() => handleSelect(option)}
                className={`p-3 cursor-pointer hover:bg-orange-500/30 transition-colors ${
                  option.name === value ? 'bg-orange-500/20' : ''
                }`}
              >
                <div className="text-white font-medium">{option.name}</div>
                <div className="text-sm text-gray-400">
                  {option.team} {option.position && `• ${option.position}`} {option.ppg && `• ${option.ppg} PPG`}
                </div>
              </div>
            ))}
            {filteredOptions.length > 100 && (
              <div className="p-3 text-center text-gray-400 text-sm">
                Showing first 100 results. Type to narrow down...
              </div>
            )}
          </div>
        )}

        {isOpen && filteredOptions.length === 0 && searchTerm && (
          <div className="absolute z-50 w-full mt-1 bg-gray-800 border border-gray-600 rounded-lg shadow-xl p-4 text-center text-gray-400">
            No players found matching "{searchTerm}"
          </div>
        )}
      </div>
    </div>
  );
}

export default SearchableSelect;
