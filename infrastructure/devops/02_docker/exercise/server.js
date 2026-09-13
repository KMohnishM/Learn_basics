const express = require('express');
const { Pool } = require('pg');

const app = express();
const port = 3000;

// Connect to Postgres using the environment variables we will set in docker-compose
const pool = new Pool({
  user: process.env.PGUSER || 'myuser',
  host: process.env.PGHOST || 'db', // The service name in docker-compose!
  database: process.env.PGDATABASE || 'mydb',
  password: process.env.PGPASSWORD || 'secret',
  port: 5432,
});

app.get('/', async (req, res) => {
  try {
    const result = await pool.query('SELECT NOW() as time');
    res.json({
      status: 'success',
      message: 'Connected to the database!',
      db_time: result.rows[0].time
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.listen(port, () => {
  console.log(`Legacy App listening at http://localhost:${port}`);
});
