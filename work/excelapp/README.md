# Customer Data Processing Pipeline

A full-stack application for processing customer transaction data from Excel files with automatic geolocation enrichment and comprehensive analytics.

## Features

- **Excel File Processing**: Upload Excel files with Transactions, Customers, and Products sheets
- **Data Validation**: Automatic validation of required columns and data structure
- **Geolocation Enrichment**: Automatic coordinate assignment using OpenStreetMap API with smart fallback
- **Address History Tracking**: Detect and track customer address changes over time
- **Analytics Generation**: Customer ranking, category spending, and top spenders analysis
- **Multi-format Output**: Download processed data as Excel and summary reports as Word documents
- **Upload Logging**: SQLite database logging of all file uploads with metadata

## Tech Stack

- **Backend**: Python Flask with pandas, openpyxl, requests, python-docx
- **Frontend**: React.js with modern CSS
- **Database**: SQLite for upload logging
- **API**: OpenStreetMap Nominatim for geolocation

## Installation

### Prerequisites

- Python 3.7+
- Node.js 14+
- npm

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install Node.js dependencies:
   ```bash
   npm install
   ```

## Running the Application

### Manual Setup

1. **Start the Backend Server**:
   ```bash
   cd backend
   python app.py
   ```
   Backend will run on `http://127.0.0.1:5001`

2. **Start the Frontend Development Server**:
   ```bash
   cd frontend
   npm start
   ```
   Frontend will run on `http://localhost:3000`

### Automatic Setup

Use the provided script to start both servers automatically:

```bash
./start.sh
```

## Usage

1. Open your browser and navigate to `http://localhost:3000`
2. Upload an Excel file with the following structure:
   - **Customers Sheet**: Single column with format `customer_id_name_email_dob_address_created_date`
   - **Products Sheet**: Columns `product_code`, `product_name`, `category`, `unit_price`
   - **Transactions Sheet**: Columns `transaction_id`, `customer_id`, `transaction_date`, `product_code`, `amount`, `payment_type`
3. Click "Upload & Process" to process the file
4. Download the processed Excel file and Word summary report

## Data Processing Features

### Address History Tracking
- Chronologically tracks customer address changes
- Maintains complete address history for each customer

### Geolocation Enrichment
- Real addresses: Uses OpenStreetMap Nominatim API
- Fake addresses: Automatically detects and assigns coordinates based on city/state
- Fallback system: City → State → Manual assignment

### Analytics Generated
- **Customer Ranking**: Ranks customers by total purchase value
- **Category Spending**: Total spending per customer per product category
- **Top Spenders**: Identifies highest spender in each product category
- **Revenue Analysis**: Total transactions, revenue, and customer insights

## File Structure

```
excelapp/
├── backend/
│   ├── app.py              # Main Flask application
│   ├── requirements.txt    # Python dependencies
│   ├── uploads/           # Upload directory
│   └── outputs/           # Generated files directory
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── App.jsx        # Main React app
│   │   └── App.css        # Styling
│   ├── package.json       # Node.js dependencies
│   └── public/            # Static assets
├── README.md
├── start.sh               # Automatic startup script
└── .gitignore            # Git ignore rules
```

## API Endpoints

- `POST /upload` - Upload and process Excel file
- `GET /outputs/<filename>` - Download processed files

## Error Handling

The application includes comprehensive error handling for:
- Invalid file formats
- Missing required columns
- Data validation errors
- Network connectivity issues
- Geolocation API failures

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.