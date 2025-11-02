const allowedMethods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'];

export const config = {
  api: {
    bodyParser: {
      sizeLimit: '1mb',
    },
  },
};

export default async function handler(req, res) {
  if (!allowedMethods.includes(req.method)) {
    res.setHeader('Allow', allowedMethods);
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  const base =
    process.env.API_INTERNAL_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

  if (!base) {
    return res.status(500).json({ error: 'API base not configured' });
  }

  const segments = Array.isArray(req.query.segments) ? req.query.segments : [];

  const url = new URL(`${segments.join('/')}`, base.endsWith('/') ? base : `${base}/`);

  if (req.method === 'GET' && req.url.includes('?')) {
    const search = req.url.slice(req.url.indexOf('?') + 1);
    if (search) {
      url.search = search;
    }
  }

  const headers = {
    'content-type': req.headers['content-type'] || 'application/json',
  };

  if (process.env.API_CLIENT_KEY) {
    headers['x-api-key'] = process.env.API_CLIENT_KEY;
  }

  const init = {
    method: req.method,
    headers,
  };

  if (req.method !== 'GET' && req.body) {
    const payload = typeof req.body === 'string' ? req.body : JSON.stringify(req.body);
    init.body = payload;
  }

  try {
    const response = await fetch(url, init);
    const text = await response.text();
    res.status(response.status);
    for (const [key, value] of response.headers.entries()) {
      if (key.toLowerCase() === 'content-length') continue;
      res.setHeader(key, value);
    }
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      return res.send(text ? JSON.parse(text) : {});
    }
    return res.send(text);
  } catch (error) {
    return res.status(502).json({ error: 'Upstream request failed', detail: error.message });
  }
}
