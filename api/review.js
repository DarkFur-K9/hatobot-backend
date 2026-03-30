const axios = require('axios');

module.exports = async function handler(req, res) {
  // CORS Headers
  res.setHeader('Access-Control-Allow-Credentials', true);
  res.setHeader('Access-Control-Allow-Origin', '*'); 
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
  res.setHeader('Access-Control-Allow-Headers', 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // 1. Only allow POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ success: false, error: 'Method Not Allowed' });
  }

  try {
    const { name, review } = req.body;

    if (!name || !review) {
      return res.status(400).json({ success: false, error: 'Name and review are required.' });
    }

    // 2. Load environment variables
    const token = process.env.WHATSAPP_TOKEN;
    const phoneId = process.env.PHONE_NUMBER_ID;
    const adminNum = process.env.ADMIN_NUMBER;

    if (!token || !phoneId || !adminNum) {
      console.error('Missing required environment variables');
      return res.status(500).json({ success: false, error: 'Internal Server Error' });
    }

    // 3. Send WhatsApp message to Admin via Meta Cloud API v21.0
    const url = `https://graph.facebook.com/v21.0/${phoneId}/messages`;
    
    // Format the alert message
    const messageText = `New Review on HatoBot!\nName: ${name}\nReview: ${review}`;

    const payload = {
      messaging_product: 'whatsapp',
      to: adminNum,
      type: 'text',
      text: { body: messageText }
    };

    const headers = {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json'
    };

    await axios.post(url, payload, { headers });

    // 4. Return success
    return res.status(200).json({ success: true });

  } catch (error) {
    console.error('Error sending WhatsApp message:', error.response?.data || error.message);
    // 4. Return 500 on error
    return res.status(500).json({ success: false, error: 'Internal Server Error' });
  }
};
