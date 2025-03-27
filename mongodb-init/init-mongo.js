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
  ]);

  print("Users collection created and populated with default users.");
} else {
  print("Users collection already exists. Skipping initialization.");
}
