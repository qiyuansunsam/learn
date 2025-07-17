import React, { useState } from 'react';

function FileUpload({ onUpload, disabled }) {
    const [selectedFiles, setSelectedFiles] = useState(null);

    const handleFileChange = (event) => {
        setSelectedFiles(event.target.files);
    };

    const handleSubmit = (event) => {
        event.preventDefault();
        onUpload(selectedFiles);
    };

    const getLabelText = () => {
        if (!selectedFiles || selectedFiles.length === 0) {
            return 'Choose Excel File';
        }
        return selectedFiles[0].name;
    };

    return (
        <form onSubmit={handleSubmit} className="upload-form">
            <label htmlFor="file-upload" className="custom-file-upload">
                {getLabelText()}
            </label>
            <input 
                id="file-upload" 
                type="file" 
                onChange={handleFileChange} 
                accept=".xlsx,.xls" 
            />
            <button type="submit" disabled={!selectedFiles || disabled}>
                {disabled ? 'Processing...' : 'Upload & Process'}
            </button>
        </form>
    );
}

export default FileUpload;