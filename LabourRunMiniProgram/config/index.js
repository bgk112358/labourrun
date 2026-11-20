const ENV = 'dev';

const environments = {
  dev: {
    apiBaseUrl: 'http://192.168.100.20:3000/api/v1',
    useMockLogin: true,
    mockLoginCode: 'mock:miniapp-demo',
    useMockSteps: true,
    mockSteps: 6638,
  },
  prod: {
    apiBaseUrl: 'https://api.example.com/api/v1',
    useMockLogin: false,
    mockLoginCode: '',
    useMockSteps: false,
    mockSteps: 0,
  },
};

module.exports = Object.assign(
  { env: ENV },
  environments[ENV] || environments.dev
);
