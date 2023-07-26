import request from 'sync-request';
import inject from 'light-my-request';
import server from '../express_app/server';
import { createWorker } from 'await-sync';

const awaitSync = createWorker();

const SYNC_REQUEST = process.env.SYNC_REQUEST;
const AWAIT_SYNC = process.env.AWAIT_SYNC;
const LIGHT_MY_REQUEST = process.env.LIGHT_MY_REQUEST;
const GET_REQUEST = process.env.GET_REQUEST;

console.log(LIGHT_MY_REQUEST);

const NUM_TESTS = parseInt(process.env.NUM_TESTS);
const NUM_REQUESTS = parseInt(process.env.NUM_REQUESTS);

if (SYNC_REQUEST) {
  if (GET_REQUEST) {
    for (let i = 0; i < NUM_TESTS; i++) {
      test(`sync-request GET ${i}`, () => {
        for (let j = 0; j < NUM_REQUESTS; j++) {
          const response = request(
            'GET',
            'http://127.0.0.1:5001/',
            {
              qs: { input: i },
            },
          );
          expect(
            JSON.parse(response.getBody('utf-8')).output
          ).toStrictEqual(i * 2);
        }
      });
    }
  } else {
    for (let i = 0; i < NUM_TESTS; i++) {
      test(`sync-request POST ${i}`, () => {
        for (let j = 0; j < NUM_REQUESTS; j++) {
          const response = request(
            'POST',
            'http://127.0.0.1:5001/',
            {
              json: { input: i },
            },
          );
          expect(
            JSON.parse(response.getBody('utf-8')).output
          ).toStrictEqual(i * 2);
        }
      });
    }
  }
} else if (LIGHT_MY_REQUEST) {
  if (GET_REQUEST) {
    for (let i = 0; i < NUM_TESTS; i++) {
      test(`light-my-request GET ${i}`, async () => {
        for (let j = 0; j < NUM_REQUESTS; j++) {
          const response = await inject(server, {
            method: 'GET',
            url: 'http://127.0.0.1:5001',
            query: { input: i },
          });
          const json = JSON.parse(response.payload);
          expect(json.output).toStrictEqual(i * 2);
        }
      });
    }
  } else {
    for (let i = 0; i < NUM_TESTS; i++) {
      test(`light-my-request POST ${i}`, async () => {
        for (let j = 0; j < NUM_REQUESTS; j++) {
          const response = await inject(server, {
            method: 'POST',
            url: 'http://127.0.0.1:5001',
            headers: { 'Content-Type': 'application/json' },
            payload: JSON.stringify({ input: i }),
          });
          const json = JSON.parse(response.payload);
          expect(json.output).toStrictEqual(i * 2);
        }
      });
    }
  }
} else if (AWAIT_SYNC) {
  if (GET_REQUEST) {
    for (let i = 0; i < NUM_TESTS; i++) {
      test(`await-sync GET ${i}`, () => {
        for (let j = 0; j < NUM_REQUESTS; j++) {
          const get = awaitSync(async (input) => {
            const res = await fetch(`http://127.0.0.1:5001?input=${input}`);
            const ab = await res.arrayBuffer();
            return new Uint8Array(ab);
          });
          const text = new TextDecoder().decode(get(i));
          const json = JSON.parse(text);
          expect(json.output).toStrictEqual(i * 2);
        }
      });
    }
  } else {
    for (let i = 0; i < NUM_TESTS; i++) {
      test(`await-sync POST ${i}`, async () => {
        // for (let j = 0; j < NUM_REQUESTS; j++) {
        //   const response = await inject(server, {
        //     method: 'POST',
        //     url: 'http://127.0.0.1:5001',
        //     headers: { 'Content-Type': 'application/json' },
        //     payload: JSON.stringify({ input: i }),
        //   });
        //   const json = JSON.parse(response.payload);
        //   expect(json.output).toStrictEqual(i * 2);
        // }
      });
    }
  }
} else { // fetch API
  if (GET_REQUEST) {
    for (let i = 0; i < NUM_TESTS; i++) {
      test(`fetch GET ${i}`, async () => {
        for (let j = 0; j < NUM_REQUESTS; j++) {
          const response = await fetch(
            `http://127.0.0.1:5001?input=${i}`,
            {
              method: 'GET',
            },
          );
          const json = await response.json();
          expect(json.output).toStrictEqual(i * 2);
        }
      });
    }
  } else {
    for (let i = 0; i < NUM_TESTS; i++) {
      test(`fetch POST ${i}`, async () => {
        for (let j = 0; j < NUM_REQUESTS; j++) {
          const response = await fetch(
            `http://127.0.0.1:5001`,
            {
              method: 'POST',
              body: JSON.stringify({ input: i }),
              headers: { 'Content-Type': 'application/json' },
            },
          );
          const json = await response.json();
          expect(json.output).toStrictEqual(i * 2);
        }
      });
    }
  }
}
