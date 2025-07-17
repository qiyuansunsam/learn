import React from 'react';

const API_BASE_URL = 'http://127.0.0.1:5001';

function ResultsDisplay({ results }) {
    if (!results) return null;

    const excelUrl = `${API_BASE_URL}${results.excel_url}`;
    const wordUrl = `${API_BASE_URL}${results.word_url}`;

    const isMockMode = results.message.includes('Mock geolocation employed');
    const baseMess = results.message && !isMockMode ? results.message : "";
    
    let fakeAddresses = [];
    if (isMockMode) {
        const addressPart = results.message.split('First 5 fake addresses: ')[1];
        if (addressPart) {
            fakeAddresses = addressPart.split(' | ').map(addr => addr.trim());
        }
    }

    return (
        <div className="results-container">
            <h3>✅ Success!</h3>
            <div className="results-content">
                <div className="results-message">
                    {baseMess && <p>{baseMess}</p>}
                    {isMockMode && (
                        <div className="fake-addresses">
                            <strong>Fake addresses detected - coordinates assigned according to city</strong>
                            <p></p>
                            <strong>5 sample fake Addresses:</strong>
                            <ul>
                                {results.coordinates ? (
                                    results.coordinates.slice(0, 5).map((item, index) => {
                                        const coords = item.lat && item.lon ? ` (${item.lat}, ${item.lon})` : ' (No coordinates)';
                                        const address = item.address.length > 35 ? item.address.substring(0, 35) + '...' : item.address;
                                        return <li key={index}>{address}{coords}</li>;
                                    })
                                ) : (
                                    fakeAddresses.slice(0, 5).map((addr, index) => {
                                        return <li key={index}>{addr}</li>;
                                    })
                                )}
                            </ul>
                        </div>
                    )}
                </div>
                <div className="download-links">
                    <a href={excelUrl} className="download-button excel" download>Download Excel</a>
                    <a href={wordUrl} className="download-button word" download>Download Report</a>
                </div>
            </div>
        </div>
    );
}

export default ResultsDisplay;