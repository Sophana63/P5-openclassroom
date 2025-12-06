// init-db/create-users.js 
print("Création des utilisateurs et rôles dédiés pour le projet médical");

db = db.getSiblingDB('medical_db');

// 1. Admin base
db.createUser({
  user: "admin-db",
  pwd: "Admin2025!",
  roles: [
    { role: "readWrite", db: "medical_db" },
    { role: "dbAdmin", db: "medical_db" },
    { role: "userAdmin", db: "medical_db" }
  ]
});

// 2. Application métier
db.createUser({
  user: "app-user",
  pwd: "AppMedical42",
  roles: [
    { role: "readWrite", db: "medical_db" }
  ]
});

// 3. Lecture seule
db.createUser({
  user: "read-only",
  pwd: "ReadOnly2025",
  roles: [
    { role: "read", db: "medical_db" }
  ]
});


print("Tous les 3 utilisateurs ont été créés avec succès !");
