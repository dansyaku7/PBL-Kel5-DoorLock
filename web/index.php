<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Door Lock</title>
    <link rel="stylesheet" href="style.css" type="text/css" />
</head>
<body>

    <div class="container">
        <div class="login">
        <form action="" method="POST">
            <h1>Sign In</h1>
            <hr>
            <p>Smart Door Lock</p>
            <label for="email">Username</label>
            <input type="text" id="username" name="username" placeholder="username" required>
            <label for="password">Password</label>
            <input type="password" id="password" name="password" placeholder="password" required>
            <button type="submit" class="btn" name="login">Sign In</button>

        <div class="register-link">
            <p>Don't have an account?</p>
            <a href="regis.php">Sign Up</a>
        </div>
        </form>
    </div>
    

        <div class="right">
            <img src="IoT-Smart-Lock-Vulnerability.jpg" alt="Smart Door Lock Image">
        </div>
    </div>
</body>
</html>

<?php
include "database.php";

if (isset($_POST["login"])) {
    // 'mysqli_real_escape_string' untuk perlindungan dasar dari serangan SQL injection
    $username = mysqli_real_escape_string($connection, $_POST["username"]);
    $password = mysqli_real_escape_string($connection, $_POST["password"]);

    // Query SQL untuk memeriksa login
    $query = "SELECT * FROM users WHERE username = '$username' AND password = '$password'";
    $result = mysqli_query($connection, $query);

    if (mysqli_num_rows($result) > 0) {
        // Login berhasil, simpan username dalam sesi
        $_SESSION['username'] = $username;
        header("Location: home.html");
        exit();
    } else {
        echo "<script>  
        alert('Username dan Password Salah!');
        window.location = 'index.php';
        </script>";
    }
}
?>
