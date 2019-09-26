const functions = require('firebase-functions');
const admin = require('firebase-admin');
const express = require('express');
const cors = require('cors');
admin.initializeApp();

const app = express();

app.use(cors({origin: true}));

/**
 * To retrieve the database as a JSON on web client
 */
app.all('/:limit', (req, res) => {
    let limit;
    try {
        limit = parseInt(req.params.limit);
        admin.database().ref('data').limitToFirst(limit).once('value')
            .then(resultSnapshot => res.send(resultSnapshot.toJSON()))
            .catch(err => {
                console.error(err);
                res.sendStatus(500);
            });
    } catch (e) {
        console.error(e);
        res.sendStatus(500);
    }
});
app.all('/', (req, res) => {
    admin.database().ref('data').once('value')
        .then(resultSnapshot => res.send(resultSnapshot.toJSON()))
        .catch(err => {
            console.error(err);
            res.sendStatus(500);
        });
});

exports.data = functions.runWith({timeoutSeconds: 540}).region('asia-east2').https.onRequest(app);
