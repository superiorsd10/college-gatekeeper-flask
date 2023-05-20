// // Create and Deploy Your First Cloud Functions
// // https://firebase.google.com/docs/functions/write-firebase-functions
//
// exports.helloWorld = functions.https.onRequest((request, response) => {
//   functions.logger.info("Hello logs!", {structuredData: true});
//   response.send("Hello from Firebase!");
// });

const currentDate = new Date();
const currentDay = currentDate.getDate();
const currentMonth = currentDate.getMonth() + 1;
const currentYear = currentDate.getFullYear();

const date = `${currentDay}-${currentMonth}-${currentYear}`;

const functions = require("firebase-functions");
const admin = require("firebase-admin");
admin.initializeApp();

const firestore = admin.firestore();

exports.recordDefaulters = functions.pubsub
    .schedule("00 23 * * *")
    .timeZone("Asia/Kolkata")
    .onRun((context) => {
      const collectionRef = firestore
          .collection("data")
          .doc(date)
          .collection("entries");

      return collectionRef
          .get()
          .then((snapshot) => {
            if (snapshot.empty) {
              console.log("No documents found in the collection.");
              return null;
            }

            const batch = firestore.batch();
            const defaulterCollectionRef = firestore.collection("defaulters");

            snapshot.forEach((doc) => {
              const defaulterDocRef = defaulterCollectionRef.doc(doc.id);
              batch.set(defaulterDocRef, doc.data());
            });

            return batch.commit();
          })
          .then(() => {
            console.log("Defaulters recorded successfully.");
            return null;
          })
          .catch((error) => {
            console.error("Error recording defaulters:", error);
            throw new functions.https.HttpsError(
                "internal",
                "An error occurred while recording defaulters."
            );
          });
    });
