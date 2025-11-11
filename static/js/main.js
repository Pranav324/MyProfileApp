// main.js - client-side validation, UI, and improved logout handling
document.addEventListener('DOMContentLoaded', function(){

  // Password visibility toggles
  document.querySelectorAll('.toggle-pw').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = document.getElementById(btn.dataset.target);
      if (!target) return;
      if (target.type === 'password') { target.type = 'text'; btn.textContent = '🙈'; }
      else { target.type = 'password'; btn.textContent = '👁️'; }
    });
  });

  // Password match indicator on register page
  const pw = document.getElementById('password');
  const repw = document.getElementById('repassword');
  const matchDot = document.getElementById('pw-match');
  if (pw && repw && matchDot) {
    function checkMatch() {
      if (repw.value === '') { matchDot.style.color = 'gray'; matchDot.textContent = '●'; return; }
      if (pw.value === repw.value) { matchDot.style.color = 'green'; matchDot.textContent = '✔'; }
      else { matchDot.style.color = 'red'; matchDot.textContent = '✖'; }
    }
    pw.addEventListener('input', checkMatch);
    repw.addEventListener('input', checkMatch);
  }

  // Password match indicator on reset page
  const resetForm = document.getElementById('resetForm');
  if (resetForm) {
      const pw = document.getElementById('password');
      const repw = document.getElementById('repassword');
      const matchDot = document.getElementById('pw-match');
      
      function checkMatch() {
          if (repw.value === '') {
              matchDot.className = 'match-indicator';
          } else if (pw.value === repw.value) {
              matchDot.className = 'match-indicator match';
          } else {
              matchDot.className = 'match-indicator no-match';
          }
      }
      
      pw.addEventListener('input', checkMatch);
      repw.addEventListener('input', checkMatch);
  }

  // Simple form validation on submit (register)
  const form = document.getElementById('registerForm');
  if (form) {
    form.addEventListener('submit', function(e) {
      const name = document.getElementById('name').value.trim();
      const email = document.getElementById('email').value.trim();
      const mobile = document.getElementById('mobile').value.trim();
      const username = document.getElementById('username').value.trim();
      const password = document.getElementById('password').value;

      const nameRe = /^[A-Za-z][A-Za-z ]+[A-Za-z]$/;
      const emailRe = /^[A-Za-z0-9._%+-]+@gmail\.com$/;
      const mobileRe = /^\d{10}$/;
      const usernameRe = /^[A-Za-z0-9][A-Za-z0-9._-]*@gmail\.com$/;
      const pwRe = /^(?=.*[A-Za-z])(?=.*\d)(?=.*[^A-Za-z0-9]).{6,}$/;

      let errors = [];
      if (!nameRe.test(name) || name.split(' ').length < 2) errors.push('Name invalid');
      if (!emailRe.test(email)) errors.push('Email must end with @gmail.com');
      if (!mobileRe.test(mobile)) errors.push('Mobile must be 10 digits');
      if (username !== email || !usernameRe.test(username)) errors.push('Username must match email and not start with special char');
      if (!pwRe.test(password)) errors.push('Password must contain letter, digit and special char');
      if (password !== document.getElementById('repassword').value) errors.push('Passwords do not match');

      if (errors.length) {
        e.preventDefault();
        alert('Please fix the following errors:\n' + errors.join('\n'));
      }
    });
  }

  // ----------------------------
  // Improved logout handler
  // ----------------------------
  const logoutLink = document.querySelector('a[href*="/logout"], a[href*="logout"]');
  if (logoutLink) {
      logoutLink.addEventListener('click', function(e) {
          e.preventDefault();
          
          fetch('/logout', {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json',
                  'Cache-Control': 'no-cache'
              },
              credentials: 'same-origin'
          })
          .then(response => response.json())
          .then(data => {
              // Clear any cached pages
              if ('caches' in window) {
                  caches.keys().then(names => {
                      names.forEach(name => {
                          caches.delete(name);
                      });
                  });
              }
              
              // Replace current history state and redirect
              history.replaceState(null, '', '/');
              window.location.replace(forceReload('/'));
          })
          .catch(err => {
              console.error('Logout error:', err);
              window.location.replace(forceReload('/'));
          });
      });
  }

  // ----------------------------
  // Prevent Back from leaving profile silently
  // ----------------------------
  if (window.location.pathname === '/profile') {
    // create a stable state so popstate fires when user tries to go back
    history.pushState(null, '', window.location.href);

    window.addEventListener('popstate', function(e) {
      // Show confirmation: user must logout before leaving
      const confirmLeave = confirm('You are still logged in. Please log out before navigating away. Press OK to log out and go to the homepage, Cancel to stay on this page.');
      if (confirmLeave) {
        // Perform logout and redirect
        fetch('/logout', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'same-origin'
        }).finally(() => {
          // ensure history does not allow going back to profile
          try {
            window.history.replaceState(null, '', '/');
          } catch (err) {}
          window.location.replace(forceReload('/'));
        });
      } else {
        // User chose to stay: push state again to block leaving
        history.pushState(null, '', window.location.href);
      }
    });
  }

});

// Add this to your main.js
function forceReload(url) {
    const timestamp = new Date().getTime();
    const separator = url.includes('?') ? '&' : '?';
    return `${url}${separator}_=${timestamp}`;
}
