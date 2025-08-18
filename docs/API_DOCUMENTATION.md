# 🔌 OrlandoPunx.com API Documentation

Complete API documentation for the Orlando Punk Shows platform, including Gancio API endpoints and custom integrations.

## 🎯 Base Information

**Base URL**: https://orlandopunx.com/api  
**Platform**: Gancio v1.4.4  
**Authentication**: Session-based with API tokens  
**Content-Type**: application/json  

## 📅 Events API

### Get All Events
```http
GET /api/events
```

**Parameters:**
- `start` (optional): Start date filter (YYYY-MM-DD)
- `end` (optional): End date filter (YYYY-MM-DD)
- `tags` (optional): Filter by comma-separated tags
- `places` (optional): Filter by venue IDs

**Response:**
```json
{
  "events": [
    {
      "id": 12,
      "title": "Clementine with Walking Blue, Lady Heroine, and Default Friends",
      "slug": "clementine-with-walking-blue-lady-heroine-and-default-friends",
      "description": "Underground punk show at Will's Pub",
      "start_datetime": "2025-08-18T06:00:00.000Z",
      "end_datetime": "2025-08-18T12:00:00.000Z",
      "image_path": "/media/44f0672e209d35be1dc76d49cb52ff63.jpg",
      "tags": ["punk", "hardcore"],
      "place": {
        "id": 1,
        "name": "Will's Pub",
        "address": "1042 N. Mills Ave. Orlando, FL 32803"
      }
    }
  ]
}
```

### Get Single Event
```http
GET /api/event/{slug}
```

**Response:**
```json
{
  "id": 12,
  "title": "Event Title",
  "description": "Event description with full details",
  "start_datetime": "2025-08-18T06:00:00.000Z",
  "end_datetime": "2025-08-18T12:00:00.000Z",
  "image_path": "/media/image.jpg",
  "media": [
    {
      "url": "image.jpg",
      "height": 1200,
      "width": 960,
      "name": "Event Flyer"
    }
  ],
  "tags": ["punk", "hardcore"],
  "place": {
    "id": 1,
    "name": "Will's Pub",
    "address": "1042 N. Mills Ave. Orlando, FL 32803",
    "latitude": 28.5516,
    "longitude": -81.3776
  }
}
```

### Create Event (Admin)
```http
POST /api/event
Authorization: Bearer {token}
Content-Type: application/json
```

**Payload:**
```json
{
  "title": "Event Title",
  "description": "Event description",
  "start_datetime": "2025-08-20T19:00:00.000Z",
  "end_datetime": "2025-08-20T23:00:00.000Z",
  "placeId": 1,
  "tags": ["punk", "hardcore"]
}
```

### Update Event (Admin)
```http
PUT /api/event/{id}
Authorization: Bearer {token}
```

### Delete Event (Admin)
```http
DELETE /api/event/{id}
Authorization: Bearer {token}
```

## 🏢 Venues API

### Get All Venues
```http
GET /api/places
```

**Response:**
```json
{
  "places": [
    {
      "id": 1,
      "name": "Will's Pub",
      "address": "1042 N. Mills Ave. Orlando, FL 32803",
      "latitude": 28.5516,
      "longitude": -81.3776,
      "website": "https://www.facebook.com/WillsPub"
    }
  ]
}
```

### Get Single Venue
```http
GET /api/place/{id}
```

## 🏷️ Tags API

### Get All Tags
```http
GET /api/tags
```

**Response:**
```json
{
  "tags": [
    {
      "tag": "punk",
      "count": 25,
      "color": "#ff6e40"
    },
    {
      "tag": "hardcore", 
      "count": 15,
      "color": "#424242"
    }
  ]
}
```

## 📡 RSS Feed

### Get RSS Feed
```http
GET /feed/rss
Content-Type: application/rss+xml
```

**Response:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Orlando Punk Shows</title>
    <link>https://orlandopunx.com</link>
    <description>A digital poster wall for DIY, PUNK, AND HARDCORE shows in Orlando, FL</description>
    <item>
      <title>Event Title</title>
      <link>https://orlandopunx.com/event/event-slug</link>
      <description>Event description</description>
      <pubDate>Mon, 18 Aug 2025 06:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
```

## 🔐 Authentication

### Login
```http
POST /api/auth/login
Content-Type: application/json
```

**Payload:**
```json
{
  "email": "user@example.com",
  "password": "password"
}
```

**Response:**
```json
{
  "token": "jwt-token-here",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role": "admin"
  }
}
```

### Logout
```http
POST /api/auth/logout
Authorization: Bearer {token}
```

## 🔧 Custom Endpoints

### Health Check
```http
GET /api/health
```

**Response:**
```json
{
  "status": "ok",
  "version": "1.4.4",
  "uptime": 86400,
  "database": "connected",
  "events_count": 25
}
```

### Statistics
```http
GET /api/stats
```

**Response:**
```json
{
  "events": {
    "total": 150,
    "this_month": 25,
    "upcoming": 8
  },
  "venues": {
    "total": 3,
    "active": 2
  },
  "tags": {
    "total": 12,
    "most_used": "punk"
  }
}
```

## 🔄 Event Sync Integration

### Will's Pub Sync Status
```http
GET /api/sync/willspub/status
```

**Response:**
```json
{
  "last_sync": "2025-08-18T05:30:00Z",
  "status": "success",
  "events_synced": 5,
  "next_sync": "2025-08-18T11:30:00Z"
}
```

### Manual Sync Trigger (Admin)
```http
POST /api/sync/willspub/trigger
Authorization: Bearer {token}
```

## 📊 Analytics Endpoints

### Event Views
```http
GET /api/analytics/event/{id}/views
```

### Popular Events
```http
GET /api/analytics/popular?period=month
```

**Response:**
```json
{
  "popular_events": [
    {
      "id": 12,
      "title": "Event Title",
      "views": 150,
      "shares": 25
    }
  ]
}
```

## 🌐 Federation (ActivityPub)

### Actor Profile
```http
GET /api/ap/actor
Accept: application/activity+json
```

### Outbox
```http
GET /api/ap/actor/outbox
Accept: application/activity+json
```

### Followers
```http
GET /api/ap/actor/followers
Accept: application/activity+json
```

## 📡 WebHooks

### Event Created
```
POST {webhook_url}
Content-Type: application/json
```

**Payload:**
```json
{
  "event": "event.created",
  "data": {
    "id": 12,
    "title": "Event Title",
    "start_datetime": "2025-08-18T06:00:00.000Z",
    "place": "Will's Pub"
  },
  "timestamp": "2025-08-18T05:30:00Z"
}
```

## 🔍 Search API

### Search Events
```http
GET /api/search?q={query}&type=events
```

**Parameters:**
- `q`: Search query
- `type`: "events", "places", or "all"
- `limit`: Results limit (default: 20)

## 📝 Error Handling

### Standard Error Response
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid event data provided",
    "details": {
      "field": "start_datetime",
      "issue": "Date must be in the future"
    }
  }
}
```

### Common HTTP Status Codes
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

## 🧪 Testing

### Test Event Creation
```bash
curl -X POST https://orlandopunx.com/api/event \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Event",
    "description": "Test event description",
    "start_datetime": "2025-08-20T19:00:00.000Z",
    "end_datetime": "2025-08-20T23:00:00.000Z",
    "placeId": 1,
    "tags": ["test"]
  }'
```

### Test Event Retrieval
```bash
curl -H "Accept: application/json" https://orlandopunx.com/api/events
```

## 🔗 Integration Examples

### Python Integration
```python
import requests

# Get upcoming events
response = requests.get('https://orlandopunx.com/api/events')
events = response.json()['events']

for event in events:
    print(f"{event['title']} at {event['place']['name']}")
```

### JavaScript Integration
```javascript
// Fetch events for calendar
async function getEvents() {
  const response = await fetch('https://orlandopunx.com/api/events');
  const data = await response.json();
  return data.events;
}

// Use in frontend
getEvents().then(events => {
  events.forEach(event => {
    console.log(`${event.title} - ${event.start_datetime}`);
  });
});
```

---

*For additional API support, check the Gancio documentation or contact the system administrator.*
