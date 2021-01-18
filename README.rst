=========
Blurplefy
=========

Discord application which converts images to different blurple shades or other colors.

Deploying
---------

- Set up the AWS CLI:

  https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2-linux.html

- Authenticate Docker so it can push images to an ECR registry:

  https://aws.amazon.com/ecr
  https://docs.aws.amazon.com/lambda/latest/dg/getting-started-create-function.html#gettingstarted-create-upload

- Set up or update an existing Lambda Function to use the pushed image:

  https://aws.amazon.com/lambda

  Under ``Create function`` select ``Container image``, select your image.

  Create a new execution role without any selected permissions as we don't need them.

- In the function overview under ``Designer`` on the main page select ``Add trigger``.

  Select ``API Gateway`` from the dropdown, create a new HTTP API and select ``Open`` in the security dropdown.

  Back on the main page scroll down to Environment variables, click on ``edit`` and add your Discord
  Application's ID as ``APPLICATION_CLIENT_ID`` and its public key as ``APPLICATION_PUBLIC_KEY``.

- Now to finish setting up the application scroll back to the top and click on the API Gateway you set up.

  At the bottom of the page click on ``Details`` and copy the API endpoint into your Discord Application's
  Interactions Endpoint URL so it can make use of it.
