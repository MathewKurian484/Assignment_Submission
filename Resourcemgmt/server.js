const express = require('express');
const mongoose = require('mongoose');
const multer = require('multer');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

// MongoDB connection with retry logic
const connectWithRetry = async () => {
  const mongodbUri = process.env.MONGODB_URI || 'mongodb://mongodb:27017/pdfDB';
  const maxRetries = 5;
  const retryDelay = 5000; // 5 seconds
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      console.log(`Attempting to connect to MongoDB (attempt ${attempt + 1}/${maxRetries})...`);
      await mongoose.connect(mongodbUri, {
        useNewUrlParser: true,
        useUnifiedTopology: true,
        serverSelectionTimeoutMS: 5000
      });
      console.log('Successfully connected to MongoDB');
      return;
    } catch (err) {
      console.error(`Connection attempt ${attempt + 1} failed:`, err.message);
      if (attempt < maxRetries - 1) {
        console.log(`Retrying in ${retryDelay/1000} seconds...`);
        await new Promise(resolve => setTimeout(resolve, retryDelay));
      } else {
        console.error('Max retries reached. Could not connect to MongoDB.');
        throw err;
      }
    }
  }
};

// Connect to MongoDB
connectWithRetry().catch(err => {
  console.error('MongoDB connection error:', err);
  process.exit(1);
});

const fileSchema = new mongoose.Schema({
  name: { type: String, required: true },
  contentType: { type: String, required: true },
  data: { type: Buffer, required: true },
  title: { type: String, default: '' },
  description: { type: String, default: '' },
  course: { type: String, default: '' },
  type: { type: String, default: '' },
  uploadDate: { type: Date, default: Date.now },
});
const FileModel = mongoose.model('File', fileSchema);

const storage = multer.memoryStorage();
const upload = multer({ storage });

// Upload endpoint
app.post('/upload', upload.single('file'), async (req, res) => {
  const file = new FileModel({
    name: req.body.name,
    contentType: req.file.mimetype,
    data: req.file.buffer,
    title: req.body.name || 'Untitled',
    description: req.body.description || 'No description available',
    course: req.body.course,
    type: req.body.type,
    uploadDate: new Date(),
  });
  await file.save();
  res.send({ message: 'Uploaded successfully', id: file._id });
});

// Download/preview endpoint
app.get('/file/:id', async (req, res) => {
  try {
    const file = await FileModel.findById(req.params.id);
    if (!file) {
      return res.status(404).send('File not found');
    }
    res.set('Content-Type', file.contentType);
    res.send(file.data);
  } catch (err) {
    res.status(500).send('Failed to fetch file');
  }
});

// Fetch all resources
app.get('/resources', async (req, res) => {
  try {
    const files = await FileModel.find();
    res.json(files);
  } catch (err) {
    res.status(500).send('Failed to fetch resources');
  }
});

// Delete a resource
app.delete('/resource/:id', async (req, res) => {
  try {
    await FileModel.findByIdAndDelete(req.params.id);
    res.send({ message: 'Resource deleted successfully' });
  } catch (err) {
    res.status(500).send('Failed to delete resource');
  }
});

// Update a resource
app.put('/resource/:id', async (req, res) => {
  try {
    const updatedResource = await FileModel.findByIdAndUpdate(
      req.params.id,
      {
        title: req.body.title,
        description: req.body.description,
        course: req.body.course,
      },
      { new: true }
    );
    res.json(updatedResource);
  } catch (err) {
    res.status(500).send('Failed to update resource');
  }
});


app.get('/resource/:id', async (req, res) => {
  console.log('Fetching resource with ID:', req.params.id);
  try {
    const resource = await FileModel.findById(req.params.id);
    if (!resource) {
      return res.status(404).send('Resource not found');
    }
    res.json(resource);
  } catch (err) {
    console.error('Error fetching resource:', err);
    res.status(500).send('Failed to fetch resource');
  }
});

app.listen(8001, '0.0.0.0', () => {
  console.log('Server started on http://0.0.0.0:8001');
});