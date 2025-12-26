# JSW Paint Estimator

AI-powered paint estimation system with **manual input** and **OpenCV-based automation** for accurate paint quantity and cost calculations.

## 🎯 Features

### Scenario 1: Manual Estimation
Input room dimensions manually and get instant paint calculations:
- Room dimensions (length, width, height)
- Number of doors and windows
- Paint type (interior/exterior)
- Number of coats

**Outputs:**
- Paintable area (sq ft)
- Paint required (liters)
- Product breakdown (primer, putty, paint)
- Estimated cost (₹)

### Scenario 2: OpenCV-based Automation
Upload room images for automated estimation:
- Automatic door/window detection using YOLO
- Room dimension estimation from images
- Multi-room estimation support
- Reference object calibration

**Outputs:**
- Detection results (doors, windows)
- Estimated room dimensions
- Total paint quantity for all rooms
- Product-wise breakdown
- Total estimated cost

## 🚀 Quick Start

### Installation

1. **Clone the repository**
```bash
cd JSW-Paint-Estimator
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
# Edit .env file with your settings
cp .env.example .env  # If needed
```

### Running the Application

**Development Mode:**
```bash
python app/main.py
```

Or using uvicorn directly:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Using the run script:**
```bash
chmod +x run.sh
./run.sh
```

The API will be available at: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Alternative Docs: `http://localhost:8000/redoc`

## 📚 API Endpoints

### Health Check
```bash
GET /health
```

### Manual Estimation (Scenario 1)

**Single Room:**
```bash
POST /api/v1/estimate/manual
Content-Type: application/json

{
  "room": {
    "length": 12.0,
    "width": 10.0,
    "height": 10.0,
    "num_doors": 1,
    "num_windows": 2
  },
  "paint_type": "interior",
  "num_coats": 2,
  "include_ceiling": false
}
```

**Multiple Rooms:**
```bash
POST /api/v1/estimate/manual/multi-room
```

### CV-based Estimation (Scenario 2)

**Single Room:**
```bash
POST /api/v1/estimate/cv/single-room
Content-Type: multipart/form-data

Form Data:
- image: <room-image-file>
- room_type: "bedroom"
- paint_type: "interior"
- num_coats: 2
```

**Multiple Rooms:**
```bash
POST /api/v1/estimate/cv/multi-room
```

**Check Model Status:**
```bash
GET /api/v1/estimate/cv/model-status
```

## 🧪 Testing

Run all tests:
```bash
pytest tests/ -v
```

Run specific test files:
```bash
pytest tests/test_manual.py -v
pytest tests/test_calculation.py -v
pytest tests/test_cv.py -v
```

## 📁 Project Structure

```
JSW-Paint-Estimator/
├── api/                      # API endpoints
│   ├── manual_estimation.py  # Scenario 1 endpoints
│   ├── cv_estimation.py      # Scenario 2 endpoints
│   └── health.py            # Health check
├── app/
│   └── main.py              # FastAPI application
├── services/                 # Business logic
│   ├── calculation_engine.py # Paint calculations
│   ├── cv_pipeline.py       # OpenCV processing
│   ├── detection.py         # YOLO object detection
│   └── scaling.py           # Pixel-to-real scaling
├── schemas/                  # Pydantic models
│   ├── manual_models.py     # Manual input schemas
│   ├── cv_models.py         # CV input schemas
│   └── output_models.py     # Response schemas
├── utils/                    # Utilities
│   ├── math_utils.py        # Calculation utilities
│   ├── image_utils.py       # Image processing
│   └── response_utils.py    # Response formatting
├── cv_models/
│   └── yolo/                # YOLO model weights
├── tests/                    # Test suite
├── .env                      # Environment variables
├── requirements.txt          # Dependencies
└── README.md
```

## 🎨 Paint Products

The system includes JSW paint products catalog:

**Interior Paints:**
- Premium Emulsion (₹450/liter, 130 sq ft coverage)
- Luxury Emulsion (₹380/liter, 120 sq ft coverage)
- Distemper (₹180/liter, 140 sq ft coverage)

**Exterior Paints:**
- Weather Proof (₹520/liter, 110 sq ft coverage)
- Apex Ultima (₹680/liter, 100 sq ft coverage)

**Primers & Putty:**
- Interior Primer (₹220/liter)
- Exterior Primer (₹280/liter)
- Wall Putty (₹35/kg, 20 sq ft coverage)

*Note: Update `utils/paint_config.json` with actual prices and products.*

## 🔧 Configuration

Edit `.env` file:

```env
# Application
APP_NAME="JSW Paint Estimator"
PORT=8000

# YOLO Model
YOLO_MODEL_PATH="cv_models/yolo/best.pt"

# Paint Configuration
PAINT_CONFIG_PATH="utils/paint_config.json"

# Standard Measurements
STANDARD_DOOR_HEIGHT=7.0
STANDARD_DOOR_WIDTH=3.0
```

## 🐳 Docker Deployment

Build and run with Docker:

```bash
docker build -t jsw-paint-estimator .
docker run -p 8000:8000 jsw-paint-estimator
```

## 📝 YOLO Model Setup

For OpenCV-based detection, you need a YOLO model trained for door/window detection:

1. Place your trained model at: `cv_models/yolo/best.pt`
2. Or train a custom model using `scripts/train_detector.py`

**Without YOLO:** The system will use fallback edge-based detection.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest tests/ -v`
5. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🔗 Links

- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## 💡 Usage Examples

### Example 1: Manual Estimation

```python
import requests

url = "http://localhost:8000/api/v1/estimate/manual"
data = {
    "room": {
        "length": 15,
        "width": 12,
        "height": 10,
        "num_doors": 2,
        "num_windows": 3
    },
    "paint_type": "interior",
    "num_coats": 2
}

response = requests.post(url, json=data)
print(response.json())
```

### Example 2: CV-based Estimation

```python
import requests

url = "http://localhost:8000/api/v1/estimate/cv/single-room"

with open("room_image.jpg", "rb") as f:
    files = {"image": f}
    data = {
        "room_type": "bedroom",
        "paint_type": "interior",
        "num_coats": 2
    }
    response = requests.post(url, files=files, data=data)
    print(response.json())
```

## 📞 Support

For issues and questions, please open an issue on GitHub.

---

**Built with:** FastAPI • OpenCV • YOLOv8 • Pydantic
