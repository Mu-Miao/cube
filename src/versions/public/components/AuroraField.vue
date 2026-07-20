<template>
  <div class="aurora-field" aria-hidden="true">
    <span class="aurora-field__orb aurora-field__orb--blue"></span>
    <span class="aurora-field__orb aurora-field__orb--green"></span>
    <span class="aurora-field__orb aurora-field__orb--violet"></span>
  </div>
</template>

<style scoped>
.aurora-field {
  position: fixed;
  inset: 0;
  z-index: -2;
  overflow: hidden;
  background:
    radial-gradient(circle at 24% 16%, rgba(48, 86, 142, 0.2), transparent 34%),
    radial-gradient(circle at 78% 30%, rgba(55, 112, 90, 0.14), transparent 30%),
    linear-gradient(180deg, #050506, #0a0a0d 46%, #030304);
}

.aurora-field::after {
  content: '';
  position: absolute;
  inset: 0;
  background-image: radial-gradient(rgba(255, 255, 255, 0.075) 1px, transparent 1px);
  background-size: 24px 24px;
  mask-image: linear-gradient(to bottom, transparent, #000 12%, #000 72%, transparent);
  opacity: 0.34;
}

.aurora-field__orb {
  position: absolute;
  width: 48vw;
  aspect-ratio: 1;
  border-radius: 50%;
  filter: blur(62px);
  opacity: 0.42;
  animation: liquid-drift 16s ease-in-out infinite alternate;
}

.aurora-field__orb--blue {
  top: 7%;
  right: 2%;
  background: rgba(71, 152, 255, 0.2);
}

.aurora-field__orb--green {
  left: 12%;
  bottom: 4%;
  background: rgba(64, 214, 132, 0.12);
  animation-delay: -4s;
}

.aurora-field__orb--violet {
  right: 22%;
  bottom: 18%;
  width: 32vw;
  background: rgba(149, 129, 255, 0.1);
  animation-delay: -8s;
}

@keyframes liquid-drift {
  from {
    transform: translate3d(-2%, -2%, 0) scale(0.94);
  }

  to {
    transform: translate3d(3%, 4%, 0) scale(1.08);
  }
}
</style>
