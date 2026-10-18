import csv, os
D = "data"

skills = [
("S01","Python",1,30,"py|python3|python programming|python language"),
("S02","Git and GitHub",1,8,"git|github|version control"),
("S03","SQL",1,20,"sql|mysql|postgresql|database queries"),
("S04","HTML",1,15,"html5|html|web pages markup"),
("S05","CSS",1,20,"css3|css|styling|stylesheets"),
("S06","JavaScript",2,40,"js|javascript|es6|java script"),
("S07","Responsive Design",2,10,"responsive|mobile friendly design|media queries"),
("S08","Tailwind CSS",2,12,"tailwind|tailwindcss"),
("S09","React",3,40,"reactjs|react.js|react js"),
("S10","Node.js",2,25,"nodejs|node|node js"),
("S11","REST APIs",2,15,"rest|api|apis|restful api|web services"),
("S12","Express.js",2,20,"express|expressjs|express js"),
("S13","MongoDB",2,15,"mongo|mongodb|nosql"),
("S14","Authentication",3,15,"auth|login system|jwt|user authentication"),
("S15","Web Deployment",2,10,"deployment|hosting|deploy website|netlify|vercel"),
("S16","Command Line and Linux",1,10,"terminal|cli|bash|linux|command line"),
("S17","Statistics Basics",2,30,"stats|statistics|descriptive statistics"),
("S18","Linear Algebra Basics",2,20,"linear algebra|matrices|vectors"),
("S19","NumPy",1,12,"numpy|np|numerical python"),
("S20","Pandas",2,20,"pandas|pd|dataframes"),
("S21","Data Visualization",2,15,"matplotlib|seaborn|plotting|charts|data viz"),
("S22","Data Cleaning",2,12,"data cleaning|data preprocessing|missing values"),
("S23","Exploratory Data Analysis",2,15,"eda|data exploration|data analysis"),
("S24","Machine Learning Basics",3,40,"ml|machine learning|sklearn|scikit-learn"),
("S25","Feature Engineering",3,15,"feature selection|feature extraction"),
("S26","Model Evaluation",3,12,"model validation|metrics|cross validation"),
("S27","Deep Learning Basics",3,40,"dl|deep learning|neural networks|tensorflow|pytorch"),
("S28","Probability Basics",2,20,"probability|probability theory"),
("S29","Object-Oriented Programming",2,20,"oop|oops|object oriented|classes and objects"),
("S30","Data Structures",2,50,"dsa|ds|data structures|arrays linked lists trees"),
("S31","Algorithms",3,50,"algos|algorithms|sorting searching|graph algorithms"),
("S32","Time and Space Complexity",2,10,"big o|complexity analysis|time complexity"),
("S33","Recursion and Dynamic Programming",3,30,"dp|dynamic programming|recursion"),
("S34","Operating Systems Basics",3,30,"os|operating systems|process scheduling"),
("S35","Computer Networks Basics",2,25,"cn|computer networks|networking|tcp ip"),
("S36","DBMS Concepts",2,20,"dbms|database management|normalization"),
("S37","System Design Basics",3,30,"system design|hld|scalability"),
("S38","FastAPI",2,20,"fastapi|fast api|python backend"),
("S39","Software Testing",2,12,"testing|unit testing|pytest"),
("S40","Docker Basics",2,12,"docker|containers|containerization"),
("S41","Problem Solving Practice",2,60,"leetcode|coding practice|competitive programming|problem solving"),
("S42","SDLC and Agile Basics",1,6,"sdlc|agile|scrum|software development life cycle"),
]

W,DS,SE = "Web Developer","Data Scientist","Software Engineer"
cs = [
(W,"S04",1),(W,"S05",1),(W,"S06",1),(W,"S02",1),(W,"S07",1),(W,"S09",1),(W,"S11",1),
(W,"S16",2),(W,"S10",2),(W,"S12",2),(W,"S13",2),(W,"S03",2),(W,"S14",2),(W,"S15",2),
(W,"S08",3),(W,"S01",3),
(DS,"S01",1),(DS,"S19",1),(DS,"S20",1),(DS,"S03",1),(DS,"S21",1),(DS,"S22",1),(DS,"S23",1),
(DS,"S17",1),(DS,"S24",1),(DS,"S26",1),(DS,"S28",2),(DS,"S18",2),(DS,"S25",2),(DS,"S02",2),
(DS,"S27",3),(DS,"S16",3),
(SE,"S01",1),(SE,"S29",1),(SE,"S30",1),(SE,"S31",1),(SE,"S32",1),(SE,"S41",1),(SE,"S02",1),
(SE,"S33",2),(SE,"S34",2),(SE,"S35",2),(SE,"S36",2),(SE,"S37",2),(SE,"S38",2),(SE,"S39",2),
(SE,"S16",2),(SE,"S03",2),(SE,"S40",3),(SE,"S11",3),(SE,"S42",3),
]

pre = [
("S05","S04"),("S06","S04"),("S07","S05"),("S08","S05"),("S09","S06"),("S10","S06"),
("S11","S06"),("S12","S10"),("S13","S10"),("S14","S11"),("S14","S12"),("S15","S02"),("S15","S06"),
("S19","S01"),("S20","S19"),("S21","S20"),("S22","S20"),("S23","S21"),("S23","S22"),
("S24","S20"),("S24","S17"),("S24","S18"),("S24","S28"),("S25","S24"),("S26","S24"),
("S27","S24"),("S27","S18"),
("S29","S01"),("S32","S01"),("S30","S01"),("S30","S32"),("S31","S30"),("S31","S32"),
("S33","S31"),("S41","S30"),("S34","S16"),("S36","S03"),("S37","S36"),("S37","S35"),("S37","S11"),
("S38","S01"),("S38","S11"),("S39","S01"),("S39","S29"),("S40","S16"),
]

MDN="https://developer.mozilla.org/en-US/docs/"
K="https://www.kaggle.com/learn/"
G="https://www.geeksforgeeks.org/"
res = [
("S01","Python Official Tutorial","docs","https://docs.python.org/3/tutorial/","beginner",300),
("S01","Kaggle Learn: Python","course",K+"python","beginner",300),
("S02","Pro Git Book","book","https://git-scm.com/book/en/v2","beginner",240),
("S02","GitHub Skills","course","https://skills.github.com/","beginner",180),
("S03","SQLBolt Interactive Lessons","course","https://sqlbolt.com/","beginner",180),
("S03","Kaggle Learn: Intro to SQL","course",K+"intro-to-sql","beginner",240),
("S04","MDN: Learn HTML","docs",MDN+"Learn/HTML","beginner",300),
("S04","freeCodeCamp Curriculum","course","https://www.freecodecamp.org/learn/","beginner",600),
("S05","MDN: Learn CSS","docs",MDN+"Learn/CSS","beginner",400),
("S05","Flexbox Froggy","practice","https://flexboxfroggy.com/","beginner",60),
("S06","JavaScript.info","docs","https://javascript.info/","beginner",900),
("S06","MDN: JavaScript Guide","docs",MDN+"Web/JavaScript/Guide","intermediate",600),
("S07","MDN: Responsive Design","docs",MDN+"Learn/CSS/CSS_layout/Responsive_Design","intermediate",90),
("S07","web.dev: Learn Responsive Design","course","https://web.dev/learn/design","intermediate",180),
("S08","Tailwind CSS Docs","docs","https://tailwindcss.com/docs","beginner",180),
("S08","Tailwind: Utility-First Fundamentals","docs","https://tailwindcss.com/docs/utility-first","beginner",30),
("S09","React: Learn","docs","https://react.dev/learn","beginner",600),
("S09","React Tutorial: Tic-Tac-Toe","practice","https://react.dev/learn/tutorial-tic-tac-toe","beginner",90),
("S10","Node.js: Learn","docs","https://nodejs.org/en/learn","beginner",300),
("S10","The Odin Project: NodeJS","course","https://www.theodinproject.com/paths/full-stack-javascript/courses/nodejs","intermediate",600),
("S11","MDN: HTTP Overview","docs",MDN+"Web/HTTP/Overview","beginner",60),
("S11","RESTful API Tutorial","docs","https://restfulapi.net/","intermediate",120),
("S12","Express: Getting Started","docs","https://expressjs.com/en/starter/installing.html","beginner",180),
("S12","MDN: Express Tutorial","docs",MDN+"Learn/Server-side/Express_Nodejs","intermediate",360),
("S13","MongoDB University","course","https://learn.mongodb.com/","beginner",240),
("S13","MongoDB Manual","docs","https://www.mongodb.com/docs/manual/","intermediate",180),
("S14","OWASP Authentication Cheat Sheet","docs","https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html","intermediate",60),
("S14","JWT Introduction","docs","https://jwt.io/introduction","beginner",30),
("S15","Render Docs","docs","https://render.com/docs","beginner",60),
("S15","Vercel Docs","docs","https://vercel.com/docs","beginner",60),
("S16","Linux Journey","course","https://linuxjourney.com/","beginner",360),
("S16","MIT: The Missing Semester","course","https://missing.csail.mit.edu/","intermediate",600),
("S17","Khan Academy: Statistics and Probability","course","https://www.khanacademy.org/math/statistics-probability","beginner",900),
("S17","StatQuest (YouTube)","video","https://www.youtube.com/@statquest","beginner",600),
("S18","Khan Academy: Linear Algebra","course","https://www.khanacademy.org/math/linear-algebra","beginner",800),
("S18","3Blue1Brown: Linear Algebra","video","https://www.3blue1brown.com/topics/linear-algebra","beginner",180),
("S19","NumPy: Absolute Beginners","docs","https://numpy.org/doc/stable/user/absolute_beginners.html","beginner",90),
("S19","NumPy: Quickstart","docs","https://numpy.org/doc/stable/user/quickstart.html","beginner",120),
("S20","Kaggle Learn: Pandas","course",K+"pandas","beginner",240),
("S20","Pandas: 10 Minutes to Pandas","docs","https://pandas.pydata.org/docs/user_guide/10min.html","beginner",60),
("S21","Kaggle Learn: Data Visualization","course",K+"data-visualization","beginner",240),
("S21","Matplotlib Tutorials","docs","https://matplotlib.org/stable/tutorials/index.html","intermediate",180),
("S22","Kaggle Learn: Data Cleaning","course",K+"data-cleaning","beginner",240),
("S22","Pandas: Working with Missing Data","docs","https://pandas.pydata.org/docs/user_guide/missing_data.html","intermediate",60),
("S23","Seaborn Tutorial","docs","https://seaborn.pydata.org/tutorial.html","intermediate",180),
("S23","Kaggle Datasets (practice)","practice","https://www.kaggle.com/datasets","beginner",240),
("S24","Kaggle Learn: Intro to Machine Learning","course",K+"intro-to-machine-learning","beginner",180),
("S24","scikit-learn User Guide","docs","https://scikit-learn.org/stable/user_guide.html","intermediate",600),
("S25","Kaggle Learn: Feature Engineering","course",K+"feature-engineering","intermediate",300),
("S25","scikit-learn: Preprocessing","docs","https://scikit-learn.org/stable/modules/preprocessing.html","intermediate",120),
("S26","scikit-learn: Model Evaluation","docs","https://scikit-learn.org/stable/modules/model_evaluation.html","intermediate",120),
("S26","Kaggle Learn: Intermediate ML","course",K+"intermediate-machine-learning","intermediate",240),
("S27","Kaggle Learn: Intro to Deep Learning","course",K+"intro-to-deep-learning","intermediate",240),
("S27","3Blue1Brown: Neural Networks","video","https://www.3blue1brown.com/topics/neural-networks","beginner",100),
("S28","Khan Academy: Probability","course","https://www.khanacademy.org/math/statistics-probability/probability-library","beginner",400),
("S28","Seeing Theory","tool","https://seeing-theory.brown.edu/","beginner",120),
("S29","Python Docs: Classes","docs","https://docs.python.org/3/tutorial/classes.html","beginner",90),
("S29","Real Python: OOP in Python","docs","https://realpython.com/python3-object-oriented-programming/","intermediate",120),
("S30","VisuAlgo","tool","https://visualgo.net/","beginner",240),
("S30","GeeksforGeeks: Data Structures","docs",G+"data-structures/","beginner",600),
("S31","GeeksforGeeks: Algorithms","docs",G+"fundamentals-of-algorithms/","intermediate",600),
("S31","CS50 (Harvard)","course","https://cs50.harvard.edu/x/","beginner",1200),
("S32","GeeksforGeeks: Analysis of Algorithms","docs",G+"analysis-of-algorithms/","beginner",120),
("S32","Big-O Cheat Sheet","docs","https://www.bigocheatsheet.com/","beginner",30),
("S33","GeeksforGeeks: Dynamic Programming","docs",G+"dynamic-programming/","intermediate",600),
("S33","GeeksforGeeks: Recursion","docs",G+"recursion/","beginner",180),
("S34","Operating Systems: Three Easy Pieces","book","https://pages.cs.wisc.edu/~remzi/OSTEP/","advanced",1200),
("S34","GeeksforGeeks: Operating Systems","docs",G+"operating-systems/","intermediate",600),
("S35","GeeksforGeeks: Computer Networks","docs",G+"computer-network-tutorials/","beginner",600),
("S35","Cloudflare Learning Center","docs","https://www.cloudflare.com/learning/","beginner",180),
("S36","GeeksforGeeks: DBMS","docs",G+"dbms/","beginner",480),
("S36","PostgreSQL Tutorial","docs","https://www.postgresqltutorial.com/","intermediate",300),
("S37","System Design Primer","docs","https://github.com/donnemartin/system-design-primer","advanced",900),
("S37","GeeksforGeeks: System Design","docs",G+"system-design-tutorial/","intermediate",600),
("S38","FastAPI Tutorial","docs","https://fastapi.tiangolo.com/tutorial/","beginner",360),
("S38","FastAPI: First Steps","docs","https://fastapi.tiangolo.com/tutorial/first-steps/","beginner",30),
("S39","pytest: Getting Started","docs","https://docs.pytest.org/en/stable/getting-started.html","beginner",60),
("S39","Python Docs: unittest","docs","https://docs.python.org/3/library/unittest.html","intermediate",90),
("S40","Docker: Get Started","docs","https://docs.docker.com/get-started/","beginner",120),
("S40","Play with Docker Labs","practice","https://labs.play-with-docker.com/","beginner",120),
("S41","LeetCode Problemset","practice","https://leetcode.com/problemset/","intermediate",3000),
("S41","NeetCode Roadmap","practice","https://neetcode.io/roadmap","intermediate",2400),
("S42","Atlassian: Agile Coach","docs","https://www.atlassian.com/agile","beginner",90),
("S42","GeeksforGeeks: SDLC","docs",G+"software-development-life-cycle-sdlc/","beginner",60),
]

web = """mujhe websites banane hain
I want to become a web developer
mujhe frontend developer banna hai
I want to build websites and web apps
mujhe apni khud ki website banani hai
Want to learn HTML CSS and JavaScript to get a job
mujhe React seekhna hai aur job lena hai
I want to become a full stack web developer
mujhe full stack developer banna hai
I am interested in designing and building web pages
websites ka frontend aur backend dono seekhna hai
I want to create responsive websites for clients
mujhe freelancing mein websites banana hai
I want to learn web development from scratch
mujhe web development seekhni hai bilkul zero se
I want to work as a React developer
I want to build my own portfolio website
mujhe apna portfolio website banana hai
I like making user interfaces for websites
mujhe UI wali websites banana pasand hai
I want to be a MERN stack developer
mujhe MERN stack seekhna hai
I want a job as a frontend engineer in a startup
startup mein web developer ki job chahiye
I want to learn Node.js and build web apps
mujhe Node.js aur Express seekhna hai
I want to make e-commerce websites
mujhe online shopping website banani hai
I want to become a website developer and freelancer
mujhe website developer ban ke freelancing karni hai
I want to learn how websites work and build one
mujhe samajhna hai ki websites kaise bante hain
I want to build web applications with login and database
mujhe login wali web application banani hai
I want to learn JavaScript for web development
mujhe JavaScript seekh ke web developer banna hai
I want to create modern looking websites
mujhe achhi dikhne wali websites design karni hain
I aim to become a frontend developer within six months
mujhe 6 mahine mein frontend developer banna hai
I want to learn to host and deploy websites
mujhe website live karni seekhni hai""".split("\n")

ds = """mujhe data scientist banna hai
I want to become a data scientist
mujhe machine learning seekhni hai
I want to build machine learning models
I want to analyze data and find insights
mujhe data analysis karna pasand hai
mujhe AI aur ML mein career banana hai
I want to work in artificial intelligence
I want to learn Python for data science
mujhe Python se data science seekhni hai
I want to become a data analyst
mujhe data analyst ki job chahiye
I want to predict things using data
mujhe data se predictions karni hain
I want to learn pandas numpy and scikit-learn
mujhe pandas aur numpy seekhna hai
I am interested in deep learning and neural networks
mujhe deep learning seekhni hai
I want to make dashboards and visualizations from data
mujhe data visualization seekhni hai
I want to work with statistics and machine learning
mujhe statistics aur ML dono seekhne hain
I want to be an ML engineer
mujhe machine learning engineer banna hai
I want to solve real problems with data
mujhe Kaggle competitions mein participate karna hai
I want to learn how recommendation systems are built
mujhe data science mein masters ki taiyari karni hai
I want to build AI models for healthcare data
mujhe data se kaam karne wali job chahiye
I want to learn data science from scratch
mujhe data science zero se seekhni hai
I want to become a business analyst who uses data
I want a career in data science and analytics
mujhe analytics mein career banana hai
I want to learn how to clean and explore datasets
mujhe datasets clean karna aur samajhna seekhna hai
I want to train models and evaluate them
mujhe model train karna aur test karna seekhna hai""".split("\n")

se = """mujhe software engineer banna hai
I want to become a software engineer
mujhe Google jaisi company mein SDE banna hai
I want to crack coding interviews at top companies
mujhe DSA seekhna hai placement ke liye
I want to improve my data structures and algorithms
mujhe coding interview ki preparation karni hai
I want to be a software developer in a product company
mujhe product based company mein job chahiye
I want to learn computer science fundamentals
mujhe core CS subjects seekhne hain
I want to learn system design
mujhe system design seekhna hai
I want to become a backend engineer
mujhe backend developer banna hai
I want to learn operating systems and networks for interviews
mujhe OS aur DBMS aur networks interview ke liye padhne hain
I want to get better at problem solving
mujhe competitive programming seekhni hai
I want to build scalable software systems
mujhe bade software systems banana seekhna hai
I want to learn object oriented programming and design
mujhe OOP aur software design seekhna hai
I want to become an SDE intern
mujhe SDE internship chahiye
I want to learn writing clean tested code
mujhe achha code likhna aur testing seekhni hai
I want to prepare for campus placements
mujhe campus placement ki taiyari karni hai
I want to learn algorithms and dynamic programming
mujhe dynamic programming seekhni hai
I want to build APIs and backend services
mujhe APIs aur backend services banani hain
I want to become a strong programmer
mujhe achha programmer banna hai
I want a career in software development
mujhe software development mein career banana hai
I want to understand how software is built in companies
mujhe samajhna hai ki companies mein software kaise banta hai
I want to learn Docker and deployment as a software engineer
mujhe LeetCode practice karni hai""".split("\n")

os.makedirs(D, exist_ok=True)
def w(name, header, rows):
    with open(f"{D}/{name}", "w", newline="", encoding="utf-8") as f:
        c = csv.writer(f); c.writerow(header); c.writerows(rows)

w("skills.csv", ["skill_id","skill_name","difficulty","est_hours","aliases"], skills)
w("career_skills.csv", ["career","skill_id","priority"], cs)
w("prerequisites.csv", ["skill_id","prereq_skill_id"], pre)
w("goal_texts.csv", ["text","career"], [(t,W) for t in web]+[(t,DS) for t in ds]+[(t,SE) for t in se])
w("resources.csv", ["resource_id","skill_id","title","type","url","level","duration_min","is_free"],
  [(f"R{i+1:02d}",s,t,ty,u,l,d,"yes") for i,(s,t,ty,u,l,d) in enumerate(res)])
print("done")
