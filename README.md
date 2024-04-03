# Deep Face Exploration API

## Endpoints

### `GET /`

Welcome page of the API.

**Response:**

- `200 OK` on success

---

### `POST /registering_face`

Register a face with the system.

**Parameters:**

- `image`: The image file of the face to register.
- `identifier`: A unique identifier for the face.

**Response:**

- `200 OK` on success
- `400 Bad Request` if the image or identifier is not provided

---

### `POST /face_recognition`

Recognize a face in an image.

**Parameters:**

- `image`: The image file to recognize the face from.
- `analyze`: A boolean indicating whether to analyze the image.

**Response:**

- `200 OK` on success
- `400 Bad Request` if the image is not provided

---

### `POST /face_verification`

Verify a face in an image.

**Parameters:**

- `image`: The image file to verify the face from.
- `identifier`: The identifier of the face to verify.
- `analyze`: A boolean indicating whether to analyze the image.

**Response:**

- `200 OK` on success
- `400 Bad Request` if the image or identifier is not provided

---

### `GET /test_connection`

Test the connection to the database.

**Response:**

- `200 OK` on success

---

### `GET /rebuild_voyager`

Rebuild the voyager index.

**Response:**

- `200 OK` on success

---

### `POST /find_face_voyager`

Find a face in the voyager index.

**Parameters:**

- `embedding_image`: The embedding of the image to find.

**Response:**

- `200 OK` on success


## Installing and Running a Service Using Docker

Follow these steps to build and run your Docker container:

1. **Clone this repository**
   ```bash
   git clone https://github.com/AkhmadRamadani/deepface-exploration.git
   ```
2. **Navigate to the directory**
   ```bash
   cd deepface-exploration
   ```
3. **Build the Docker image**
   ```bash
   docker build
   ```
4. **Run the Docker**
   ```bash
   docker-compose up -d
   ``` 
