<div align="center">
<h1>audio_guestbook</h1>
<p>audio guestbook running on raspberry Pi</p>
</div>

<div align="center">
  <img src="https://github.com/Jibus22/audio_guestbook/assets/59167486/2eba4e5f-9d6c-4ba6-9ac6-d41bcbccf583" width="350"  alt="rasphone1" />
  <img src="https://github.com/Jibus22/audio_guestbook/assets/59167486/483e6f5c-9e07-497e-a4cd-a1e04338d72f" width="350"  alt="rasphone4" />
  <img src="https://github.com/Jibus22/audio_guestbook/assets/59167486/6a0d6034-5b4f-4006-833f-05d93a550f79" width="350"  alt="rasphone2" />
  <img src="https://github.com/Jibus22/audio_guestbook/assets/59167486/23c0d0c7-e8ab-4140-9886-c16d715931ca" width="350"  alt="rasphone3" />
</div>

---

After picking up the phone the user is welcomed by an audio announce presenting the menu.

The **main menu** allows to:
- key 0: redirection to main menu and announce the menu
- key 1: record an audio message for 60 seconds max
- key 2: randomly play an already recorded audio
- key 3: jump to a secondary menu

The **secondary menu** allows to:
- key 1: audio announce sub-menu A and jump to it
- key 2: audio announce sub-menu B and jump to it
- key 3: audio announce sub-menu C and jump to it

The **sub-menu** A allows to:
- key 1: play an audio
- ...

etc.

Overall, the device allows to play a menu, play a random recorded audio, record an audio and jump to a menu/sub-menu.
A keycode allows to shutdown the device.

---

The phone keys are connected to the adafruit keypad
