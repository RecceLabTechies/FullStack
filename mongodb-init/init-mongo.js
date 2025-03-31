db = db.getSiblingDB("test_database");

// Check if the users collection exists
const collections = db.getCollectionNames();
const usersCollectionExists = collections.includes("users");

// If the users collection doesn't exist, create it and insert the default users
if (!usersCollectionExists) {
  print("Users collection does not exist. Creating it with default users...");

  // Insert the default admin user and other users from CSV
  db.users.insertMany([
    {
      username: "master admin",
      email: "admin@recce.com",
      role: "root",
      company: "reccelabs",
      password: "Admin@123",
      chart_access: true,
      report_generation_access: true,
      user_management_access: true,
    },
    {
      username: "guest",
      email: "guest@recce.com",
      role: "member",
      company: "reccelabs",
      password: "Admin@123",
      chart_access: true,
      report_generation_access: true,
      user_management_access: false,
    },
  ]);

  print("Users collection created and populated with default users.");
} else {
  print("Users collection already exists. Skipping initialization.");
}

// Check if the campaign_performance collection exists
const campaignCollectionExists = collections.includes("campaign_performance");

// If the campaign_performance collection doesn't exist, create it and set up schema
if (!campaignCollectionExists) {
  print("Campaign performance collection does not exist. Creating it...");

  // Create a validator for the collection to enforce schema
  db.createCollection("campaign_performance", {
    validator: {
      $jsonSchema: {
        bsonType: "object",
        required: [
          "date",
          "campaign_id",
          "channel",
          "age_group",
          "ad_spend",
          "views",
          "leads",
          "new_accounts",
          "country",
          "revenue",
        ],
        properties: {
          date: { bsonType: "date" },
          campaign_id: { bsonType: "string" },
          channel: { bsonType: "string" },
          age_group: { bsonType: "string" },
          ad_spend: { bsonType: "double" },
          views: { bsonType: "double" },
          leads: { bsonType: "double" },
          new_accounts: { bsonType: "double" },
          country: { bsonType: "string" },
          revenue: { bsonType: "double" },
        },
      },
    },
  });

  print("Campaign performance collection created with schema validation.");
} else {
  print(
    "Campaign performance collection already exists. Skipping initialization."
  );
}
