# How to start Transcription Service as a Linux service?

- Make sure you follow all the steps in the `README.md` file in the main project directory, section `Installation and setup (containerized)`.
- Copy the file `service/transcription.service` to `/etc/systemd/system` on your server.
- Edit this file to add

  - user
  - path to the project directory

- To start the service, run `systemctl start transcription`.
- To stop the service run `systemctl stop transcription`.
- To start the service at server boot, run `systemctl enable transcription`.