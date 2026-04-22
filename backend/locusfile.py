from locust import HttpUser, task, between


class SomagomLoadTester(HttpUser):
    # ইউজার ১ থেকে ৩ সেকেন্ডের মধ্যে পরবর্তী একশন নিবে
    wait_time = between(1, 3)

    

    @task(5) # ৫ গুণ বেশি ইউজার প্রোডাক্ট লিস্ট দেখবে
    def get_all_products(self):
        self.client.get("/api/products/products/") # আপনার এপিআই এন্ডপয়েন্ট দিন

    @task(2)
    def get_product_detail(self):
        # আইডি ১ থেকে ১০০ এর মধ্যে যেকোনো একটি প্রোডাক্ট দেখা
        slug="persevering-bandwidth-monitored-hub-70628c73" # এখানে আপনি যেকোনো প্রোডাক্টের স্লাগ ব্যবহার করতে পারেন
        self.client.get(f"/api/products/products/{slug}/") # আপনার এপিআই এন্ডপয়েন্ট দিন
    