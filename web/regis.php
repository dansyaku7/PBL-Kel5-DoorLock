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
            <h1>Sign Up</h1>
            <hr>
            <p>Smart Door Lock</p>
            <label for="email">Email</label>
            <input type="text" id="email" name="email" placeholder="example@gmail.com" required>
            <label for="email">Username</label>
            <input type="text" id="username" name="username" placeholder="username" required>
            <label for="password">Password</label>
            <input type="password" id="password" name="password" placeholder="password" required>
            <button type="submit" class="btn" name="submit">Sign Up</button>
        <div class="register-link">
            <p>Already have an account?</p>
            <a href="index.php">Sign In</a>
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

// memeriksa koneksi database
if (isset($_POST['submit'])) {
    $email = $_POST['email'];
    $username = $_POST['username'];
    $password = $_POST['password'];

    // untuk memeriksa apakah username sudah terdaftar
    $cek_user = mysqli_query($connection, "SELECT * FROM users WHERE username = '$username'");
    $cek_login = mysqli_num_rows($cek_user);

    if ($cek_login > 0) {
        echo "<script> 
            alert('Username Telah Terdaftar');
            window.location = 'regis.php';
            </script>";
    } else {
        // eksekusi operasi INSERT
        $insert_query = "INSERT INTO users (email, username, password) VALUES ('$email', '$username', '$password')";
        $result = mysqli_query($connection, $insert_query);

        //'$result' untuk memeriksa apakah operasi INSERT berhasil atau gagal
        if ($result) {
            echo "<script>  
            alert('Data Berhasil Dikirim');
            window.location = 'index.php';
            </script>";
        } else {
            echo "Gagal menambahkan data: " . mysqli_error($connection);
        }
    }
}
?>

