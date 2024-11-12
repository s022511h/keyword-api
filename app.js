const express = require('express');
const MongoClient = require('mongodb').MongoClient;
const cors = require('cors');  // 
const fetch = require('node-fetch');  // Import fetch for making HTTP requests to Contensis API

const app = express();
const port = 3000;

const url = 'mongodb://localhost:27017';
const dbName = 'KeywordDB';

// Enable CORS for all routes
app.use(cors());

// Enable parsing of JSON requests
app.use(express.json());

// MongoDB endpoint to fetch keywords
app.get('/keywords/:type', async (req, res) => {
  const type = req.params.type;
  const client = new MongoClient(url);

  try {
    await client.connect();
    const db = client.db(dbName);
    const collection = db.collection(type);
    const keywords = await collection.find({}).toArray();
    res.json(keywords);
  } finally {
    await client.close();
  }
});

// New API endpoint to send optimized content to Contensis CMS
app.post('/contensis/submit', async (req, res) => {
  const optimizedContent = req.body.optimizedContent;

  try {
    const response = await fetch('https://your-contensis-cms-url/api/your-endpoint', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer your_token',  // Replace with actual token
      },
      body: JSON.stringify({
        content: optimizedContent,  
      }),
    });
    const result = await response.json();
    res.send(result);  
  } catch (error) {
    res.status(500).send('Error submitting content to Contensis');
  }
});


app.listen(port, () => {
  console.log(`App running on port ${port}`);
});
