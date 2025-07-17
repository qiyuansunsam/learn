import React, { useState } from 'react';
import FileUpload from './components/FileUpload';
import ResultsDisplay from './components/ResultsDisplay';
import Spinner from './components/Spinner';
import './App.css';

function App() {
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState(null);
    const [results, setResults] = useState(null);

    const handleUpload = async (files) => {
        if (!files || files.length === 0) {
            setError('Please select files first.');
            return;
        }

        setUploading(true);
        setError(null);
        setResults(null);

        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append('files[]', files[i]);
        }

        try {
            const response = await fetch('http://127.0.0.1:5001/upload', {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'An unknown error occurred.');
            }

            setResults(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="container">
            <header>
                <h1>Customer Data Processing Pipeline</h1>
                <p>Upload your Excel file containing Transactions, Customers, and Products sheets.</p>
            </header>
            
            <main>
                <FileUpload onUpload={handleUpload} disabled={uploading} />
                {uploading && <Spinner />}
                {error && <div className="error-message">{error}</div>}
                {results && <ResultsDisplay results={results} />}
            </main>
        </div>
    );
}

export default App;